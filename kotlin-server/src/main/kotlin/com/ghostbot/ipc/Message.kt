package com.ghostbot.ipc

import com.ghostbot.rootLogger
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import kotlinx.serialization.json.put
import java.nio.charset.Charset
import java.util.logging.Level

/**
 * Port of GhostBot/IPC/message.py `Command` enum.
 * Values are the wire numbers used in the plain-text heartbeat protocol.
 */
enum class Command(val value: Int) {
    ERROR(-2),
    EXIT(-1),
    INFO(1),
    INFO_CHAR(2),
    INFO_AUTOLOGIN(3),
    START(10),
    STOP(20),
    CONFIG(30),
    CONFIG_GET(31),
    CONFIG_SET(32),
    CONFIG_AUTOLOGIN_GET(33),
    CONFIG_AUTOLOGIN_SET(34),
    CONFIG_AUTOLOGIN_DELETE(35),
    OPEN_CLIENT(40),
    CLOSE_CLIENT(41),
    LOG(100),
    SERVER_HEARTBEAT(200),
    ;

    companion object {
        /** Python `Command.from_str` — look up by name, case-insensitive. */
        fun fromStr(command: String?): Command? =
            entries.find { it.name.equals(command, ignoreCase = true) }

        /** Python `Command.from_value` — look up by wire value. */
        fun fromValue(value: String): Command? =
            entries.find { it.value == value.toIntOrNull() }
    }
}

/**
 * Port of GhostBot/IPC/message.py `Message`.
 *
 * Wire format is JSON: `{"command": "<lowercase-name>", "target": <string|object|null>}`.
 * `target` may be a plain string, a JSON object, or null.
 */
class Message(
    val command: Command,
    val target: Any? = null,
) {
    override fun toString(): String {
        val obj = buildJsonObject {
            put("command", command.name.lowercase())
            put("target", target.toJsonElement())
        }
        return obj.toString()
    }

    fun encode(charset: Charset = Charsets.UTF_8): ByteArray = toString().toByteArray(charset)

    /** Target as a dict (the Python `message.target['char']` accesses). */
    fun targetAsDict(): Map<String, Any?>? =
        (target as? Map<*, *>)?.entries?.associate { (it.key as String) to it.value }

    /** Target as a string (the Python `message.target` when it's a char name). */
    fun targetAsString(): String? = target as? String

    companion object {
        private val json = Json { ignoreUnknownKeys = true }

        /**
         * Port of `Message.from_json`. Returns null on decode failure (mirroring
         * the Python behaviour of logging and returning None).
         */
        fun fromJson(data: String): Message? {
            val trimmed = data.trim()
            if (trimmed.isEmpty()) return null
            return try {
                val obj = json.parseToJsonElement(trimmed).jsonObject
                val command = Command.fromStr(obj["command"]?.jsonPrimitive?.content)
                if (command == null) {
                    rootLogger.warning("Message: unknown command in message: $data")
                    return null
                }
                Message(command, obj["target"]?.targetValue())
            } catch (e: Exception) {
                rootLogger.warning("Message: Error decoding message to JSON: String [$data]")
                rootLogger.log(Level.WARNING, "Message decode error", e)
                null
            }
        }

        /**
         * Port of `Message.from_json_handling_multiple`.
         * Python splits concatenated JSON objects on `}{` (rewritten to a sentinel first).
         */
        fun fromJsonHandlingMultiple(data: String): List<Message> =
            data.replace("}{", "}<<>>{")
                .split("<<>>")
                .mapNotNull { fromJson(it) }
    }
}

private fun Any?.toJsonElement(): JsonElement = when (val v = this) {
    null -> JsonNull
    is String -> JsonPrimitive(v)
    is Boolean -> JsonPrimitive(v)
    is Number -> JsonPrimitive(v)
    is Map<*, *> -> JsonObject(v.entries.associate { (key, value) -> key.toString() to value.toJsonElement() })
    is List<*> -> JsonArray(v.map { it.toJsonElement() })
    is Pair<*, *> -> JsonArray(listOf(first.toJsonElement(), second.toJsonElement()))
    else -> JsonPrimitive(v.toString())
}

private fun JsonElement.targetValue(): Any? = when (val el = this) {
    // JsonNull IS-A JsonPrimitive in kotlinx — must be checked first.
    is JsonNull -> null
    is JsonObject -> el.entries.associate { (k, v) -> k to v.targetValue() }
    is JsonArray -> el.map { it.targetValue() }
    is JsonPrimitive -> {
        // Boolean primitives must short-circuit (their .content is "true"/"false").
        el.booleanOrNull ?: run {
            // kotlinx decodes JSON numbers as Long; Python's json.loads yields int
            // for in-range values — mirror that so round-trips compare equal.
            val l = el.longOrNull
            if (l != null) l.toIntOrNullCompat() else el.doubleOrNull ?: el.content
        }
    }
}

private fun Long.toIntOrNullCompat(): Any =
    if (this in Int.MIN_VALUE.toLong()..Int.MAX_VALUE.toLong()) this.toInt() else this
