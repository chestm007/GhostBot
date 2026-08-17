package com.ghostbot.config

import com.ghostbot.functions.InjectedLoggingMixin
import com.ghostbot.rootLogger
import org.yaml.snakeyaml.DumperOptions
import org.yaml.snakeyaml.Yaml
import java.io.File
import java.io.FileNotFoundException
import java.util.concurrent.TimeoutException

/**
 * Port of GhostBot/config.py.
 *
 * The Python uses annotated dataclasses plus a reflection-based `validate()`
 * that coerces wrong-typed values (strings from YAML) into their declared
 * types. Kotlin has no runtime annotations, so each config class validates
 * and coerces its fields explicitly. Wire/YAML compatibility is preserved:
 * `toYaml()` / `loadYaml()` produce the same documents the Python writes.
 */

typealias Bindings = LinkedHashMap<String, Any?>

private val yaml: Yaml by lazy {
    val opts = DumperOptions()
    opts.setDefaultFlowStyle(DumperOptions.FlowStyle.AUTO)
    Yaml(opts)
}

 // ---------- coercion helpers (mirror TypedConfig._try_change_type) ----------

private fun typeName(value: Any?): String = value?.javaClass?.simpleName ?: "None"

internal fun coerceInt(value: Any?, what: String): Int = when (value) {
    is Int -> value
    is Long -> value.toInt()
    is Double -> value.toInt()
    is String -> value.trim().toIntOrNull() ?: throw IllegalStateException(
        "config: $what is an unexpected type.\nexpected int, got ${typeName(value)}"
    )
    else -> throw IllegalStateException(
        "config: $what is an unexpected type.\nexpected int, got ${typeName(value)}"
    )
}

internal fun coerceFloat(value: Any?, what: String): Double = when (value) {
    is Double -> value
    is Int -> value.toDouble()
    is Long -> value.toDouble()
    is String -> value.trim().toDoubleOrNull() ?: throw IllegalStateException(
        "config: $what is an unexpected type.\nexpected float, got ${typeName(value)}"
    )
    else -> throw IllegalStateException(
        "config: $what is an unexpected type.\nexpected float, got ${typeName(value)}"
    )
}

internal fun coerceBool(value: Any?, what: String): Boolean = when (value) {
    is Boolean -> value
    is String -> when (value.trim().lowercase()) {
        "false" -> false
        else -> value.trim().toBoolean()
    }
    is Number -> value.toInt() != 0
    else -> throw IllegalStateException(
        "config: $what is an unexpected type.\nexpected bool, got ${typeName(value)}"
    )
}

/** Coerce a `tuple[int, int]` location: pair, list, int-array or "x y" string. */
internal fun coerceSpot(value: Any?, what: String): Pair<Int, Int> = when (value) {
    is Pair<*, *> -> (coerceInt(value.first, "$what.x") to coerceInt(value.second, "$what.y"))
    is List<*> -> {
        if (value.size != 2) throw spotTypeError(value, what)
        (coerceInt(value[0], "$what.x") to coerceInt(value[1], "$what.y"))
    }
    is IntArray -> (value[0] to value[1])
    is String -> {
        val parts = value.trim().split(Regex("\\s+"))
        if (parts.size != 2) throw spotTypeError(value, what)
        (coerceInt(parts[0], "$what.x") to coerceInt(parts[1], "$what.y"))
    }
    else -> throw spotTypeError(value, what)
}

private fun spotTypeError(value: Any?, what: String) = IllegalStateException(
    "config: $what is an unexpected type.\n" +
        "expected tuple[int, int], got ${
            when (value) {
                is Boolean -> "bool"
                null -> "None"
                else -> value.javaClass.simpleName
            }
        }"
)

/** Serialize a spot for YAML (Python tuples dump as lists). */
internal fun spotToYaml(value: Any?): Any? = when (value) {
    is Pair<*, *> -> listOf(value.first, value.second)
    else -> value
}

internal fun coerceKeyInterval(value: Any?, what: String): List<Any?> = when (value) {
    is List<*> -> value.map { it as Any? }
    else -> throw IllegalStateException(
        "config: $what is an unexpected type.\nexpected list, got ${value?.javaClass?.simpleName ?: "None"}"
    )
}

// ---------- lenient converters for YAML-sourced values ----------

internal fun toIntValue(value: Any?): Int? = when (value) {
    is Int -> value
    is Long -> value.toInt()
    is Double -> value.toInt()
    is String -> value.trim().toIntOrNull()
    else -> null
}

internal fun toDoubleValue(value: Any?): Double? = when (value) {
    is Double -> value
    is Int -> value.toDouble()
    is Long -> value.toDouble()
    is String -> value.trim().toDoubleOrNull()
    else -> null
}

internal fun toBoolValue(value: Any?): Boolean? = when (value) {
    is Boolean -> value
    is String -> when (value.trim().lowercase()) {
        "false" -> false
        else -> value.trim().toBoolean()
    }
    is Number -> value.toInt() != 0
    else -> null
}

internal fun toSpotValue(value: Any?): Any? = when (value) {
    is Pair<*, *> -> (toIntValue(value.first) ?: value.first) to (toIntValue(value.second) ?: value.second)
    is List<*> -> {
        val ints = value.map { toIntValue(it) ?: it }
        if (ints.size == 2 && ints.all { it is Int }) ints[0] as Int to ints[1] as Int else ints
    }
    is String, is Int, is Long, is Double -> value
    null -> null
    else -> value
}

internal fun toBindings(value: Any?): Bindings? = (value as? Map<*, *>)?.entries
    ?.associate { (it.key as String) to it.value }?.let { LinkedHashMap(it) }

// ---------- function configs ----------

abstract class FunctionConfig {
    /** Mirror of `TypedConfig.validate` — subclasses coerce their own fields. */
    abstract fun validate()

    /** YAML-serializable representation (used by toYaml/equals). */
    abstract fun toMap(): Map<String, Any?>
}

class AttackConfig(
    var attacks: List<List<Any?>>? = null,
    var bindings: Any? = null,
    var stuckInterval: Any? = null,
    var battleManaThreshold: Any? = null,
    var battleHpThreshold: Any? = null,
    var roamDistance: Any? = null,
    var spot: Any? = null,
) : FunctionConfig() {

    /** Validated spot as a pair (after `validate()`). */
    fun spotPair(): Pair<Int, Int>? = spot?.let { coerceSpot(it, "attack.spot") }

    override fun toMap(): Map<String, Any?> = linkedMapOf(
        "attacks" to attacks,
        "bindings" to bindings,
        "stuck_interval" to stuckInterval,
        "battle_mana_threshold" to battleManaThreshold,
        "battle_hp_threshold" to battleHpThreshold,
        "roam_distance" to roamDistance,
        "spot" to spotToYaml(spot),
    )

    override fun validate() {
        if (attacks != null) attacks = attacks!!.map { coerceKeyInterval(it, "attack.attacks[i]") }
        // `bindings` as a string is silently skipped by the Python too
        if (bindings is String) bindings = null
        if (stuckInterval != null) stuckInterval = coerceInt(stuckInterval, "attack.stuck_interval")
        if (battleManaThreshold != null) battleManaThreshold = coerceFloat(battleManaThreshold, "attack.battle_mana_threshold")
        if (battleHpThreshold != null) battleHpThreshold = coerceFloat(battleHpThreshold, "attack.battle_hp_threshold")
        if (roamDistance != null) roamDistance = coerceInt(roamDistance, "attack.roam_distance")
        if (spot != null) spot = coerceSpot(spot, "attack.spot")
    }

    companion object {
        @Suppress("UNCHECKED_CAST")
        fun fromMap(data: Map<String, Any?>?): AttackConfig? {
            if (data == null) return null
            return AttackConfig(
                attacks = data["attacks"] as List<List<Any?>>?,
                bindings = data["bindings"] as Any?,
                stuckInterval = toIntValue(data["stuck_interval"]) ?: data["stuck_interval"] as? String,
                battleManaThreshold = toDoubleValue(data["battle_mana_threshold"]) ?: data["battle_mana_threshold"] as? String,
                battleHpThreshold = toDoubleValue(data["battle_hp_threshold"]) ?: data["battle_hp_threshold"] as? String,
                roamDistance = toIntValue(data["roam_distance"]) ?: data["roam_distance"] as? String,
                spot = toSpotValue(data["spot"]),
            )
        }
    }

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is FunctionConfig) return false
        return toMap() == other.toMap()
    }

    override fun hashCode(): Int = toMap().hashCode()
}

class RegenConfig(
    var bindings: Any? = Bindings().apply { put("sit", "x") },
    var hpThreshold: Any? = null,
    var manaThreshold: Any? = null,
) : FunctionConfig() {

    init {
        val b = toBindings(bindings)
        if (b != null) {
            if (b["sit"] == null) b["sit"] = "x"
            bindings = b
        }
    }

    /** Validated bindings (after `validate()`). */
    fun bindingsMap(): Bindings = toBindings(bindings) ?: Bindings()

    override fun toMap(): Map<String, Any?> = linkedMapOf(
        "bindings" to bindings,
        "hp_threshold" to hpThreshold,
        "mana_threshold" to manaThreshold,
    )

    override fun validate() {
        if (bindings is String) bindings = LinkedHashMap(mapOf("sit" to "x"))
        val b = toBindings(bindings)
        if (b != null && b["sit"] == null) b["sit"] = "x"
        if (hpThreshold != null) hpThreshold = coerceFloat(hpThreshold, "regen.hp_threshold")
        if (manaThreshold != null) manaThreshold = coerceFloat(manaThreshold, "regen.mana_threshold")
    }

    companion object {
        fun fromMap(data: Map<String, Any?>?): RegenConfig? {
            if (data == null) return null
            return RegenConfig(
                bindings = toBindings(data["bindings"]) ?: data["bindings"] ?: LinkedHashMap(mapOf("sit" to "x")),
                hpThreshold = toDoubleValue(data["hp_threshold"]) ?: data["hp_threshold"] as? String,
                manaThreshold = toDoubleValue(data["mana_threshold"]) ?: data["mana_threshold"] as? String,
            )
        }
    }

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is FunctionConfig) return false
        return toMap() == other.toMap()
    }

    override fun hashCode(): Int = toMap().hashCode()
}

class BuffConfig(
    var buffs: List<List<Any?>>? = null,
    var interval: Any? = null,
) : FunctionConfig() {

    override fun toMap(): Map<String, Any?> = linkedMapOf(
        "buffs" to buffs,
        "interval" to interval,
    )

    override fun validate() {
        if (buffs != null) buffs = buffs!!.map { coerceKeyInterval(it, "buff.buffs[i]") }
        if (interval != null) interval = coerceInt(interval, "buff.interval")
    }

    companion object {
        @Suppress("UNCHECKED_CAST")
        fun fromMap(data: Map<String, Any?>?): BuffConfig? {
            if (data == null) return null
            return BuffConfig(
                buffs = data["buffs"] as List<List<Any?>>?,
                interval = toIntValue(data["interval"]) ?: data["interval"] as? String,
            )
        }
    }

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is FunctionConfig) return false
        return toMap() == other.toMap()
    }

    override fun hashCode(): Int = toMap().hashCode()
}

class PetConfig(
    var bindings: Any? = null,
    var spawnIntervalMins: Any? = null,
    var foodIntervalMins: Any? = null,
) : FunctionConfig() {

    override fun toMap(): Map<String, Any?> = linkedMapOf(
        "bindings" to bindings,
        "spawn_interval_mins" to spawnIntervalMins,
        "food_interval_mins" to foodIntervalMins,
    )

    override fun validate() {
        if (bindings is String) bindings = null
        if (spawnIntervalMins != null) spawnIntervalMins = coerceInt(spawnIntervalMins, "pet.spawn_interval_mins")
        if (foodIntervalMins != null) foodIntervalMins = coerceInt(foodIntervalMins, "pet.food_interval_mins")
    }

    companion object {
        fun fromMap(data: Map<String, Any?>?): PetConfig? {
            if (data == null) return null
            return PetConfig(
                bindings = toBindings(data["bindings"]) ?: data["bindings"],
                spawnIntervalMins = toIntValue(data["spawn_interval_mins"]) ?: data["spawn_interval_mins"] as? String,
                foodIntervalMins = toIntValue(data["food_interval_mins"]) ?: data["food_interval_mins"] as? String,
            )
        }
    }

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is FunctionConfig) return false
        return toMap() == other.toMap()
    }

    override fun hashCode(): Int = toMap().hashCode()
}

class FairyConfig(
    var bindings: Any? = null,
    var healTeamThreshold: Any? = null,
    var healSelfThreshold: Any? = null,
    var spot: Any? = null,
) : FunctionConfig() {

    fun spotPair(): Pair<Int, Int>? = spot?.let { coerceSpot(it, "fairy.spot") }

    override fun toMap(): Map<String, Any?> = linkedMapOf(
        "bindings" to bindings,
        "heal_team_threshold" to healTeamThreshold,
        "heal_self_threshold" to healSelfThreshold,
        "spot" to spotToYaml(spot),
    )

    override fun validate() {
        if (bindings is String) bindings = null
        if (healTeamThreshold != null) healTeamThreshold = coerceFloat(healTeamThreshold, "fairy.heal_team_threshold")
        if (healSelfThreshold != null) healSelfThreshold = coerceFloat(healSelfThreshold, "fairy.heal_self_threshold")
        if (spot != null) spot = coerceSpot(spot, "fairy.spot")
    }

    companion object {
        fun fromMap(data: Map<String, Any?>?): FairyConfig? {
            if (data == null) return null
            return FairyConfig(
                bindings = toBindings(data["bindings"]) ?: data["bindings"],
                healTeamThreshold = toDoubleValue(data["heal_team_threshold"]) ?: data["heal_team_threshold"] as? String,
                healSelfThreshold = toDoubleValue(data["heal_self_threshold"]) ?: data["heal_self_threshold"] as? String,
                spot = toSpotValue(data["spot"]),
            )
        }
    }

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is FunctionConfig) return false
        return toMap() == other.toMap()
    }

    override fun hashCode(): Int = toMap().hashCode()
}

class SellConfig(
    var sellNpcName: String? = null,
    var bindings: Any? = null,
    var sellItemPos: Any? = 1,
    var sellIntervalMins: Any? = 60,
    var npcSearchSpot: Any? = null,
    var useMount: Any? = null,
    var npcSellClickSpot: Any? = null,
) : FunctionConfig() {

    init {
        if (bindings == null) bindings = LinkedHashMap(mapOf("mount" to 0))
    }

    override fun toMap(): Map<String, Any?> = linkedMapOf(
        "sell_npc_name" to sellNpcName,
        "bindings" to bindings,
        "sell_item_pos" to sellItemPos,
        "sell_interval_mins" to sellIntervalMins,
        "npc_search_spot" to spotToYaml(npcSearchSpot),
        "use_mount" to useMount,
        "npc_sell_click_spot" to spotToYaml(npcSellClickSpot),
    )

    override fun validate() {
        if (bindings is String) bindings = null
        if (sellItemPos != null) sellItemPos = coerceInt(sellItemPos, "sell.sell_item_pos")
        if (sellIntervalMins != null) sellIntervalMins = coerceInt(sellIntervalMins, "sell.sell_interval_mins")
        if (npcSearchSpot != null) npcSearchSpot = coerceSpot(npcSearchSpot, "sell.npc_search_spot")
        if (useMount != null) useMount = coerceBool(useMount, "sell.use_mount")
        if (npcSellClickSpot != null) npcSellClickSpot = coerceSpot(npcSellClickSpot, "sell.npc_sell_click_spot")
    }

    companion object {
        fun fromMap(data: Map<String, Any?>?): SellConfig? {
            if (data == null) return null
            return SellConfig(
                sellNpcName = data["sell_npc_name"]?.toString(),
                bindings = toBindings(data["bindings"]) ?: data["bindings"],
                sellItemPos = toIntValue(data["sell_item_pos"]) ?: data["sell_item_pos"] as? String,
                sellIntervalMins = toIntValue(data["sell_interval_mins"]) ?: data["sell_interval_mins"] as? String,
                npcSearchSpot = toSpotValue(data["npc_search_spot"]),
                useMount = toBoolValue(data["use_mount"]) ?: data["use_mount"] as? String,
                npcSellClickSpot = toSpotValue(data["npc_sell_click_spot"]),
            )
        }
    }

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is FunctionConfig) return false
        return toMap() == other.toMap()
    }

    override fun hashCode(): Int = toMap().hashCode()
}

class DeleteConfig(
    var deleteTrash: Any? = false,
    var interval: Any? = null,
) : FunctionConfig() {

    override fun toMap(): Map<String, Any?> = linkedMapOf(
        "delete_trash" to deleteTrash,
        "interval" to interval,
    )

    override fun validate() {
        if (deleteTrash != null) deleteTrash = coerceBool(deleteTrash, "delete.delete_trash")
        if (interval != null) interval = coerceInt(interval, "delete.interval")
    }

    companion object {
        fun fromMap(data: Map<String, Any?>?): DeleteConfig? {
            if (data == null) return null
            return DeleteConfig(
                deleteTrash = toBoolValue(data["delete_trash"]) ?: data["delete_trash"] as? String,
                interval = toIntValue(data["interval"]) ?: data["interval"] as? String,
            )
        }
    }

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is FunctionConfig) return false
        return toMap() == other.toMap()
    }

    override fun hashCode(): Int = toMap().hashCode()
}

// ---------- Config ----------

class Config(
    var attack: AttackConfig? = null,
    var buff: BuffConfig? = null,
    var fairy: FairyConfig? = null,
    var pet: PetConfig? = null,
    var regen: RegenConfig? = null,
    var sell: SellConfig? = null,
    var delete: DeleteConfig? = null,
) {
    companion object {
        private val subConfigs: Map<String, (Map<String, Any?>?) -> FunctionConfig?> = mapOf(
            "attack" to { AttackConfig.fromMap(it) },
            "buff" to { BuffConfig.fromMap(it) },
            "fairy" to { FairyConfig.fromMap(it) },
            "pet" to { PetConfig.fromMap(it) },
            "regen" to { RegenConfig.fromMap(it) },
            "sell" to { SellConfig.fromMap(it) },
            "delete" to { DeleteConfig.fromMap(it) },
        )

        /** Port of `Config.upgrade` — runs all config upgrades in order. */
        fun upgrade(data: MutableMap<String, Any?>): MutableMap<String, Any?> =
            allUpgrades.fold(data) { acc, fn -> fn(acc) }

        /** Port of `Config.load_yaml`. */
        @Suppress("UNCHECKED_CAST")
        fun loadYaml(data: Any): Config {
            val raw: Map<String, Any?> = when (data) {
                is String -> yaml.load<Map<String, Any?>>(data) ?: emptyMap()
                is Map<*, *> -> data as Map<String, Any?>
                else -> throw IllegalArgumentException("loadYaml: expected yaml string or map, got ${data.javaClass}")
            }
            val upgraded = upgrade(raw.toMutableMap())
            val config = Config()
            for ((k, v) in upgraded) {
                val parsed = (v as? Map<*, *>) as? Map<String, Any?>
                val builder = subConfigs[k] ?: throw IllegalArgumentException("$k not a valid config category")
                when (k) {
                    "attack" -> config.attack = builder(parsed) as AttackConfig?
                    "buff" -> config.buff = builder(parsed) as BuffConfig?
                    "fairy" -> config.fairy = builder(parsed) as FairyConfig?
                    "pet" -> config.pet = builder(parsed) as PetConfig?
                    "regen" -> config.regen = builder(parsed) as RegenConfig?
                    "sell" -> config.sell = builder(parsed) as SellConfig?
                    "delete" -> config.delete = builder(parsed) as DeleteConfig?
                }
            }
            config.validate()
            return config
        }

        /** Port of `Config.load_file`. */
        fun loadFile(path: String): Config {
            val file = File(path)
            if (!file.exists()) throw FileNotFoundException(path)
            return loadYaml(yaml.load<Map<String, Any?>>(file.readText()))
        }
    }

    /** Port of `Config.to_yaml`. */
    fun toYaml(): Map<String, Any?> = buildMap {
        attack?.let { put("attack", it.toMap()) }
        buff?.let { put("buff", it.toMap()) }
        fairy?.let { put("fairy", it.toMap()) }
        pet?.let { put("pet", it.toMap()) }
        regen?.let { put("regen", it.toMap()) }
        sell?.let { put("sell", it.toMap()) }
        delete?.let { put("delete", it.toMap()) }
    }

    /** Port of `Config.validate`. */
    fun validate() {
        attack?.validate()
        buff?.validate()
        fairy?.validate()
        pet?.validate()
        regen?.validate()
        sell?.validate()
        delete?.validate()
    }

    /** Port of `Config.save_file`. */
    fun saveFile(path: String) {
        File(path).writeText(yaml.dump(toYaml()))
    }

    /** Port of `Config.functions` — names of enabled sub-configs. */
    fun functions(): List<String> = toYaml().keys.toList()

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is Config) return false
        return attack == other.attack && buff == other.buff && fairy == other.fairy &&
            pet == other.pet && regen == other.regen && sell == other.sell && delete == other.delete
    }

    override fun hashCode(): Int {
        var result = attack?.hashCode() ?: 0
        result = 31 * result + (buff?.hashCode() ?: 0)
        result = 31 * result + (fairy?.hashCode() ?: 0)
        result = 31 * result + (pet?.hashCode() ?: 0)
        result = 31 * result + (regen?.hashCode() ?: 0)
        result = 31 * result + (sell?.hashCode() ?: 0)
        result = 31 * result + (delete?.hashCode() ?: 0)
        return result
    }
}

// ---------- upgrades (GhostBot/upgrades/config) ----------

internal val allUpgrades: List<(MutableMap<String, Any?>) -> MutableMap<String, Any?>> =
    listOf(::upgrade1)

/** Port of upgrades/config/upgrade_1.py — refactors regen.spot / sell.return_spot to attack/fairy.spot. */
@Suppress("UNCHECKED_CAST")
private fun upgrade1(configYaml: MutableMap<String, Any?>): MutableMap<String, Any?> {
    var attackSpot: Any? = (configYaml["attack"] as? Map<String, Any?>)?.get("spot")
    var regenSpot: Any? = (configYaml["regen"] as? Map<String, Any?>)?.get("spot")
    var sellSpot: Any? = (configYaml["sell"] as? Map<String, Any?>)?.get("return_spot")

    if (attackSpot != null && (sellSpot == null && regenSpot == null)) return configYaml

    if (regenSpot != null) {
        if (attackSpot == null) {
            if (configYaml["attack"] != null) {
                (configYaml["attack"] as MutableMap<String, Any?>)["spot"] = regenSpot
            } else if (configYaml["fairy"] != null) {
                (configYaml["fairy"] as MutableMap<String, Any?>)["spot"] = regenSpot
            }
            attackSpot = regenSpot
        }
        (configYaml["regen"] as? MutableMap<String, Any?>)?.remove("spot")
    }
    if (sellSpot != null) {
        if (attackSpot == null) {
            if (configYaml["attack"] != null) {
                (configYaml["attack"] as MutableMap<String, Any?>)["spot"] = sellSpot
            } else if (configYaml["fairy"] != null) {
                (configYaml["fairy"] as MutableMap<String, Any?>)["spot"] = sellSpot
            }
        }
        (configYaml["sell"] as? MutableMap<String, Any?>)?.remove("return_spot")
    }
    return configYaml
}

// ---------- config loaders ----------

abstract class BaseConfigLoader {
    val logger = java.util.logging.Logger.getLogger("GhostBot." + javaClass.simpleName)
    abstract val configFilename: String

    /** Computed lazily — the base constructor runs before the subclass sets
     *  [configFilename] (Kotlin init order; Python sets it before super().__init__()). */
    open val configFilePath: String by lazy { File(detectPath(), configFilename).path }

    companion object {
        /** Port of `BaseConfigLoader._detect_path`. */
        fun detectPath(): String {
            val dataPath = System.getenv("HOME") ?: System.getenv("LOCALAPPDATA")
                ?: throw FileNotFoundException("what OS u on bro?")
            val ghostbotDir = File(dataPath, "GhostBot")
            if (!ghostbotDir.exists()) ghostbotDir.mkdirs()
            return ghostbotDir.path
        }
    }
}

class ConfigLoader(private val clientName: String) : BaseConfigLoader() {
    override val configFilename: String = "$clientName.yml"

    /** Port of `ConfigLoader.load`. */
    fun load(): Config {
        logger.fine("ConfigLoader :: $clientName :: loading config")
        return try {
            val config = Config.loadFile(configFilePath)
            logger.fine("ConfigLoader :: $clientName :: config loaded")
            config
        } catch (e: FileNotFoundException) {
            logger.fine("ConfigLoader :: $clientName :: config not found, using defaults")
            val config = Config()
            save(config)
            config
        }
    }

    /** Port of `ConfigLoader.save`. */
    fun save(config: Config): Config {
        config.saveFile(configFilePath)
        return config
    }
}

class LoginDetailsConfigLoader : BaseConfigLoader() {
    override val configFilename: String = "login_details.yml"

    data class CharDetails(
        var charName: String,
        var username: String,
        var password: String,
        var server: String,
        var enabled: Boolean,
    )

    class LoginDetails(val chars: MutableMap<String, CharDetails>) {
        fun items(): Set<Map.Entry<String, CharDetails>> = chars.entries
        fun get(item: String): CharDetails? = chars[item]
        val toMap: Map<String, CharDetails> get() = chars
    }

    /** Port of `LoginDetailsConfigLoader.load`. */
    fun load(): LoginDetails {
        logger.fine("loading login config")
        val file = File(configFilePath)
        if (!file.exists()) {
            logger.fine("LoginDetailsConfigLoader :: no login config file found at $configFilePath")
            return LoginDetails(mutableMapOf())
        }
        @Suppress("UNCHECKED_CAST")
        val raw = yaml.load<Map<String, Map<String, Any?>>>(file.readText()) ?: emptyMap()
        val chars = raw.entries.associate { (name, details) ->
            name to CharDetails(
                charName = name,
                username = details["username"]?.toString() ?: "",
                password = details["password"]?.toString() ?: "",
                server = details["server"]?.toString() ?: "",
                enabled = details["enabled"]?.let {
                    if (it is Boolean) it else it.toString().toBoolean()
                } ?: false,
            )
        }.toMutableMap()
        logger.fine("LoginDetailsConfigLoader :: login config loaded")
        return LoginDetails(chars)
    }

    /** Port of `LoginDetailsConfigLoader.to_yaml` (char_name excluded). */
    fun toYaml(loginDetails: LoginDetails): Map<String, Map<String, Any?>> =
        loginDetails.chars.entries.associate { (charName, conf) ->
            charName to linkedMapOf(
                "username" to conf.username,
                "password" to conf.password,
                "server" to conf.server,
                "enabled" to conf.enabled,
            )
        }

    /** Port of `LoginDetailsConfigLoader.save`. */
    fun save(loginDetails: LoginDetails) {
        logger.fine("LoginDetailsConfigLoader :: saving login config")
        File(configFilePath).writeText(yaml.dump(toYaml(loginDetails)))
    }
}

class GhostBotServerConfigLoader : BaseConfigLoader() {
    override val configFilename: String = "ghostbot_server.yml"

    data class GhostBotConfig(val functionDebugging: Map<String, String>?)

    var config: GhostBotConfig? = null
        private set

    /** Names of function loggers (mirror of `subclasses_by_name(InjectedLoggingMixin)`). */
    private val functionNames = listOf(
        InjectedLoggingMixin::class.java.simpleName,
        "AttackContext", "Attack", "Sell", "Petfood", "Regen", "Buffs", "Fairy", "Delete", "Script",
    )

    /** Port of `GhostBotServerConfigLoader.load`. */
    fun load(): GhostBotServerConfigLoader {
        val file = File(configFilePath)
        if (file.exists()) {
            @Suppress("UNCHECKED_CAST")
            val raw = yaml.load<Map<String, Any?>>(file.readText())
            @Suppress("UNCHECKED_CAST")
            val functionDebugging = raw?.get("function_debugging") as? Map<String, String>
            config = GhostBotConfig(functionDebugging)
            logger.fine("GhostBotServerConfigLoader :: server config loaded")
        } else {
            logger.fine("GhostBotServerConfigLoader :: no server config file found at $configFilePath")
            return this
        }

        for (k in functionNames) {
            java.util.logging.Logger.getLogger("GhostBot.$k").level = java.util.logging.Level.INFO
            logger.info("setting loglevel of [$k] to [INFO]")
        }
        config?.functionDebugging?.forEach { (k, v) ->
            val level = when (v.uppercase()) {
                "SEVERE" -> java.util.logging.Level.SEVERE
                "WARNING" -> java.util.logging.Level.WARNING
                "INFO" -> java.util.logging.Level.INFO
                "CONFIG" -> java.util.logging.Level.CONFIG
                "FINE" -> java.util.logging.Level.FINE
                "FINER" -> java.util.logging.Level.FINER
                "FINEST" -> java.util.logging.Level.FINEST
                else -> null
            }
            if (level == null) {
                logger.warning("unknown log level $v for $k, keeping INFO")
                return@forEach
            }
            java.util.logging.Logger.getLogger("GhostBot.$k").level = level
            logger.info("setting loglevel of [$k] to [$level]")
        }
        return this
    }
}
