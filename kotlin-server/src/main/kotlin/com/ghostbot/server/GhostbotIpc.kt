package com.ghostbot.server

import com.ghostbot.config.Config
import com.ghostbot.config.ConfigLoader
import com.ghostbot.config.LoginDetailsConfigLoader
import com.ghostbot.controller.BotController
import com.ghostbot.ipc.Command
import com.ghostbot.ipc.IpcClient
import com.ghostbot.ipc.IpcServer
import com.ghostbot.ipc.Message
import com.ghostbot.rootLogger
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import kotlinx.serialization.json.put
import java.nio.channels.SocketChannel
import java.util.logging.Level

/**
 * Port of GhostBot/server.py — the concrete IPC server (command dispatch) and
 * the high-level IPC client used by the UX/CLI front ends.
 */

/**
 * Port of `GhostbotIPCServer`.
 */
class GhostbotIpcServer(
    val botController: BotController,
    host: String? = null,
    port: Int? = null,
    verboseLogging: Boolean = false,
) : IpcServer(host ?: "localhost", port ?: 64057, heartbeatInterval = 10) {

    var vdebug: (String) -> Unit = {}

    init {
        if (verboseLogging) {
            vdebug = { msg -> logger.info(msg) }
        }
    }

    /** Port of the `bot_controller_clients_message` property. */
    val botControllerClientsMessage: Message
       get() = Message(
           Command.INFO,
           botController.clients.entries
               .filterNot { (_, v) -> v.disconnected }
               .map { (k, _) -> k }
               .joinToString(" ")
       )

    override fun onAccept(conn: SocketChannel) {
        sendToAll(botControllerClientsMessage)
    }

    override fun dispatch(conn: SocketChannel, data: String) {
        vdebug("dispatching $data")
        for (message in Message.fromJsonHandlingMultiple(data)) {
            if (message == null) {
                logger.log(Level.FINE, "empty message")
                continue
            }
            logger.log(Level.FINE, "dispatching message: $message")
            val response = dispatchMessage(message)
            if (response != null) {
                try {
                    conn.write(java.nio.ByteBuffer.wrap(response.toString().toByteArray(Charsets.UTF_8)))
                } catch (e: Exception) {
                    logger.log(Level.SEVERE, "send error", e)
                }
            }
        }
    }

    private fun dispatchMessage(message: Message): Message? {
        return when (message.command) {
            Command.EXIT -> {
                logger.info(" exit command received")
                null
            }

            Command.START -> {
                logger.log(Level.FINE, "dispatching START")
                val target = message.target?.toString() ?: ""
                startTarget(target)
                message
            }

            Command.STOP -> {
                logger.log(Level.FINE, "dispatching STOP")
                stopTarget(message.target?.toString())
                message
            }

            Command.INFO -> {
                vdebug("dispatching INFO")
                botControllerClientsMessage
            }

            Command.INFO_CHAR -> {
                vdebug("dispatching INFO_CHAR")
                val target = message.target?.toString()
                if (target != null) {
                    vdebug("dispatching INFO containing for [$target]")
                    val client = botController.getClient(target)
                    if (client != null) {
                        Message(Command.INFO_CHAR, client.toJson())
                    } else {
                        null
                    }
                } else {
                    null
                }
            }

            Command.INFO_AUTOLOGIN -> {
                vdebug("dispatching INFO_AUTOLOGIN")
                Message(
                    Command.INFO_AUTOLOGIN,
                    botController.loginConfig?.chars?.keys?.joinToString(" ") ?: ""
                )
            }

            Command.CONFIG_GET -> {
                logger.info("dispatching CONFIG get")
                val char = message.targetAsDict()?.get("char")?.toString()
                val client = char?.let { botController.getClient(it) }
                if (client == null) {
                    logger.info("char: $char - not found")
                    return null
                }
                if (client.config == null) {
                    client.loadConfig()
                    if (client.config == null) {
                        logger.severe("client config not found for $char")
                        return null
                    }
                }
                Message(Command.CONFIG_GET, jsonEncodeString(client.config!!.toYaml()))
            }

            Command.CONFIG_AUTOLOGIN_GET -> {
                logger.info("dispatching CONFIG_AUTOLOGIN_GET")
                val char = message.targetAsDict()?.get("char")?.toString()
                val config = char?.let { botController.loginConfig?.chars?.get(it) }
                if (config != null) {
                    Message(
                        Command.CONFIG_AUTOLOGIN_GET,
                        mapOf(
                            "char_name" to config.charName,
                            "username" to config.username,
                            "password" to config.password,
                            "server" to config.server,
                            "enabled" to config.enabled,
                        )
                    )
                } else {
                    logger.info("autologin config not found for $char")
                    Message(Command.CONFIG_AUTOLOGIN_GET, emptyMap<String, Any?>())
                }
            }

            Command.CONFIG_SET -> {
                vdebug("dispatching CONFIG set")
                val char = message.targetAsDict()?.get("char")?.toString()
                val client = char?.let { botController.getClient(it) }
                if (client != null) {
                    vdebug("Setting config for ${client.name}")
                    val confRaw = message.targetAsDict()?.get("config")
                    val conf = Config.loadYaml(confRaw ?: emptyMap<String, Any?>())
                    logger.info("char: ${client.name} - set config: $conf")
                    ConfigLoader(client.name ?: "unknown").save(conf)
                    client.applyConfig(conf)
                    return message
                }
                logger.info("char: $char - not found")
                null
            }

            Command.CONFIG_AUTOLOGIN_SET -> {
                logger.info("dispatching CONFIG_AUTOLOGIN_SET")
                val target = message.targetAsDict() ?: return message
                val config = LoginDetailsConfigLoader.CharDetails(
                    charName = target["char_name"]?.toString() ?: "",
                    username = target["username"]?.toString() ?: "",
                    password = target["password"]?.toString() ?: "",
                    server = target["server"]?.toString() ?: "",
                    enabled = target["enabled"] as? Boolean ?: false,
                )
                botController.loginConfig?.chars?.set(config.charName, config)
                LoginDetailsConfigLoader().save(botController.loginConfig!!)
                message
            }

            Command.CONFIG_AUTOLOGIN_DELETE -> {
                logger.info("dispatching CONFIG_AUTOLOGIN_DELETE")
                val char = message.targetAsDict()?.get("char")?.toString()
                botController.loginConfig?.chars?.remove(char)
                botController.loginConfig?.let { LoginDetailsConfigLoader().save(it) }
                message
            }

            Command.OPEN_CLIENT -> {
                logger.info("dispatching OPEN_CLIENT")
                val char = message.targetAsDict()?.get("char")?.toString()
                if (char != null) {
                    botController.requestedLogins.add(char)
                }
                message
            }

            Command.CLOSE_CLIENT -> {
                logger.info("dispatching CLOSE_CLIENT")
                val char = message.targetAsDict()?.get("char")?.toString()
                val client = char?.let { botController.getClient(it) }
                if (client != null) {
                    client.closeWindow()
                    message
                } else {
                    logger.info("char: $char - not found")
                    null
                }
            }

            else -> null
        }
    }

    private fun startTarget(target: String) {
        val c = botController.getClient(target)
        if (c != null) {
            botController.startBot(c)
        } else {
            logger.warning("no client $target")
        }
    }

    private fun stopTarget(target: String?) {
        val c = target?.let { botController.getClient(it) }
        if (c != null) {
            botController.stopBot(c, 5)
        } else {
            logger.warning("no client $target")
        }
    }
}

// ---------- JSON helpers for config maps ----------

private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }

private fun jsonEncodeString(v: Any?): String =
    json.encodeToString(kotlinx.serialization.json.JsonElement.serializer(), v.toJsonElement())

private fun Any?.toJsonElement(): JsonElement = when (val v = this) {
    null -> kotlinx.serialization.json.JsonNull
    is String -> kotlinx.serialization.json.JsonPrimitive(v)
    is Boolean -> kotlinx.serialization.json.JsonPrimitive(v)
    is Number -> kotlinx.serialization.json.JsonPrimitive(v)
    is Map<*, *> -> buildJsonObject {
       v.forEach { (key, value) -> put(key.toString(), value.toJsonElement()) }
    }
    is List<*> -> kotlinx.serialization.json.JsonArray(v.map { it.toJsonElement() })
    is Pair<*, *> -> kotlinx.serialization.json.JsonArray(listOf(first.toJsonElement(), second.toJsonElement()))
    else -> kotlinx.serialization.json.JsonPrimitive(v.toString())
}

// ---------- client ----------

/**
 * Port of `GhostbotIPCClient`.
 */
class GhostbotIpcClient(
    host: String = "localhost",
    port: Int = 64057,
) : IpcClient(host, port) {

    companion object {
        private val json = Json { ignoreUnknownKeys = true }
    }

    private val callbacks: Map<Command, MutableList<(Message) -> Any?>> =
        Command.entries.associateWith { mutableListOf() }

    /** Port of `GhostbotIPCClient.send` — fire and forget (errors logged). */
    fun send(data: Message) {
        try {
            logger.log(Level.FINE, "sending $data")
            sendMessage(data)
        } catch (e: java.net.ConnectException) {
            logger.severe("server offline?")
        } catch (e: Exception) {
            logger.log(Level.SEVERE, "send error", e)
        }
    }

    fun addCallback(command: Command, callback: (Message) -> Any?) {
        logger.log(Level.FINE, "registering callback for $command")
        callbacks.getValue(command).add(callback)
    }

    fun delCallback(command: Command, callback: (Message) -> Any?) {
        logger.log(Level.FINE, "unregistering callback for $command")
        callbacks.getValue(command).remove(callback)
    }

    override fun dispatchRaw(data: ByteArray) {
        val text = data.toString(Charsets.UTF_8)
        // heartbeat (raw int on the wire)
        if (Command.fromValue(text.trim()) == Command.SERVER_HEARTBEAT) {
            logger.log(Level.FINE, "received HEARTBEAT")
            return
        }
        for (message in Message.fromJsonHandlingMultiple(text)) {
            if (message == null) {
                logger.log(Level.FINE, "received empty message")
                continue
            }
            logger.log(Level.FINE, "dispatching callback for $message")
            val cbs = callbacks[message.command] ?: continue
            if (cbs.isEmpty()) {
                logger.log(Level.FINE, "No callback set for ${message.command}")
                continue
            }
            for (cb in cbs) cb(message)
        }
    }

    fun shutdownServer() { send(Message(Command.EXIT)) }

    fun listChars(): List<String> {
        logger.info("${javaClass.simpleName}: sending list chars message")
        val response = sendAndWait(Message(Command.INFO))
        return response?.target?.toString()?.split(" ")?.filter { it.isNotEmpty() } ?: emptyList()
    }

    fun startBot(target: String) {
        logger.info("${javaClass.simpleName}: sending start bot message for :$target")
        send(Message(Command.START, target))
    }

    fun stopBot(target: String) {
        logger.info("${javaClass.simpleName}: sending stop bot message for :$target")
        send(Message(Command.STOP, target))
    }

    fun charInfo(target: String): String {
        logger.log(Level.FINE, "${javaClass.simpleName}: sending char info message for :$target")
        return sendAndWait(Message(Command.INFO_CHAR, target))?.target?.toString().orEmpty()
    }

    fun getConfig(target: String) {
        logger.info("${javaClass.simpleName}: sending get config message for :$target")
        send(Message(Command.CONFIG_GET, mapOf("action" to "get", "char" to target)))
    }

    fun getConfigAutologin(target: String) {
        logger.info("${javaClass.simpleName}: sending get autologin config message for :$target")
        send(Message(Command.CONFIG_AUTOLOGIN_GET, mapOf("action" to "get", "char" to target)))
    }

    fun setConfig(target: String, config: Config) {
        logger.info("${javaClass.simpleName}: sending set config message for :$target")
        send(Message(Command.CONFIG_SET, mapOf("action" to "set", "char" to target, "config" to config.toYaml())))
    }

    fun setConfigAutologin(config: LoginDetailsConfigLoader.CharDetails) {
        logger.info("${javaClass.simpleName}: sending set autologin config message for :${config.charName}")
        send(
            Message(
                Command.CONFIG_AUTOLOGIN_SET,
                mapOf(
                    "char_name" to config.charName,
                    "username" to config.username,
                    "password" to config.password,
                    "server" to config.server,
                    "enabled" to config.enabled,
                )
            )
        )
    }

    fun deleteConfigAutologin(target: String) {
        logger.info("${javaClass.simpleName}: sending delete config autologin message for :$target")
        send(Message(Command.CONFIG_AUTOLOGIN_DELETE, mapOf("action" to "delete", "char" to target)))
    }

    fun listCharsAutologin(): List<String> {
        logger.info("${javaClass.simpleName}: sending list chars autologin message")
        val response = sendAndWait(Message(Command.INFO_AUTOLOGIN))
        return response?.target?.toString()?.split(" ")?.filter { it.isNotEmpty() } ?: emptyList()
    }

    fun closeClient(target: String) {
        logger.info("${javaClass.simpleName}: sending close client message for :$target")
        send(Message(Command.CLOSE_CLIENT, mapOf("action" to "close", "char" to target)))
    }

    fun openClient(target: String) {
        logger.info("${javaClass.simpleName}: sending open client message for :$target")
        send(Message(Command.OPEN_CLIENT, mapOf("action" to "open", "char" to target)))
    }

    /**
     * Send [message] and wait (up to 5s) for the first non-heartbeat response.
     * The Python client's request/response pattern is implicit (the server
     * replies on the same socket); this makes it explicit and testable.
     */
    fun sendAndWait(message: Message, timeoutMs: Long = 5000): Message? {
        val latch = java.util.concurrent.CountDownLatch(1)
        var response: Message? = null
        val cb: (Message) -> Any? = { m ->
            response = m
            latch.countDown()
            Unit
        }
        val cmd = message.command
        addCallback(cmd, cb)
        try {
            send(message)
            latch.await(timeoutMs, java.util.concurrent.TimeUnit.MILLISECONDS)
        } finally {
            delCallback(cmd, cb)
        }
        return response
    }
}
