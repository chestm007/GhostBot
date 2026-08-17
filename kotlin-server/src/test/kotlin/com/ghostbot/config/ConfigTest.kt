package com.ghostbot.config

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertThrows
import org.junit.jupiter.api.io.TempDir
import java.nio.file.Path

/**
 * Port of the runnable parts of tests/test_config.py: type coercion on
 * validate(), the string-spot parser, the unfixable-spot error, the
 * return_spot upgrade, the autologin yaml round trip and none-not-stringified.
 */
class ConfigTest {

    @Test
    fun `loads config and parses types properly`() {
        val config = Config(
            fairy = FairyConfig(
                bindings = LinkedHashMap(mapOf("heal" to 6)),
                healSelfThreshold = "0.75",
                healTeamThreshold = "0.5",
            ),
            attack = AttackConfig(
                bindings = LinkedHashMap(mapOf("battle_hp_pot" to "F1")),
                attacks = listOf(listOf(1, 1000), listOf(2, 1400)),
                stuckInterval = "4",
                battleManaThreshold = "0.56",
                battleHpThreshold = 0.75,
                roamDistance = "40",
                spot = (123 to "456"),
            ),
            buff = BuffConfig(
                buffs = listOf(listOf(7, 2000)),
                interval = "10",
            ),
            pet = PetConfig(
                bindings = LinkedHashMap(mapOf("spawn" to "E", "food" to 9)),
                foodIntervalMins = 55,
                spawnIntervalMins = "55",
            ),
            regen = RegenConfig(
                bindings = LinkedHashMap(mapOf("hp_pot" to "Q", "mana_pot" to "W", "sit" to "X")),
                hpThreshold = "0.75",
                manaThreshold = 0.75,
            ),
            sell = SellConfig(
                sellNpcName = "Mr Guy Man",
                useMount = "false",
                npcSellClickSpot = (100 to 200),
                npcSearchSpot = listOf("123", 456),
            ),
        )

        config.validate()
        assertTrue(config.fairy!!.healSelfThreshold is Double)
        assertEquals(0.75, config.fairy!!.healSelfThreshold as Double)
        assertTrue(config.attack!!.battleManaThreshold is Double)
        assertFalse(config.sell!!.useMount as Boolean)
        assertTrue(config.buff!!.interval is Int)
        assertEquals(10, config.buff!!.interval as Int)
        assertEquals(123 to 456, config.attack!!.spot as Pair<Int, Int>)
        assertEquals(100 to 200, config.sell!!.npcSellClickSpot as Pair<Int, Int>)
        assertEquals(4, config.attack!!.stuckInterval as Int)
        assertEquals(40, config.attack!!.roamDistance as Int)
        assertEquals(0.75, config.attack!!.battleHpThreshold as Double)
    }

    @Test
    fun `errors on unfixable return spot`() {
        val dumbConfig = Config(
            attack = AttackConfig(
                attacks = listOf(listOf(1, 1000)),
                spot = false,
            )
        )
        val e = assertThrows<IllegalStateException> { dumbConfig.validate() }
        assertTrue(e.message!!.contains("tuple[int, int], got bool"), e.message)
    }

    @Test
    fun `parses string spot`() {
        val stringSpotConfig = Config(
            attack = AttackConfig(
                attacks = listOf(listOf(1, 1000)),
                spot = "123 -123",
            )
        )
        stringSpotConfig.validate()
        assertTrue(stringSpotConfig.attack!!.spot is Pair<*, *>)
        assertEquals(123 to -123, stringSpotConfig.attack!!.spot as Pair<Int, Int>)
    }

    @Test
    fun `upgrade moves return spot to attack spot`() {
        val configStr = """
            sell:
              sell_npc_name: Mr Guy Man
              return_spot:
              - 100
              - 200
            attack:
              attacks:
              - - 1
                - 1000
        """.trimIndent()

        val config = Config.loadYaml(configStr)
        assertEquals(100 to 200, config.attack!!.spot as Pair<Int, Int>)
    }

    @Test
    fun `autologin config`() {
        val loginDetails = LoginDetailsConfigLoader.LoginDetails(
            LinkedHashMap(
                mapOf(
                    "char1" to LoginDetailsConfigLoader.CharDetails(
                        charName = "char1",
                        username = "username",
                        password = "password",
                        server = "light_in_the_darkness",
                        enabled = false,
                    )
                )
            )
        )

        assertEquals("username", loginDetails.get("char1")!!.username)
        assertEquals("password", loginDetails.get("char1")!!.password)
        assertEquals("light_in_the_darkness", loginDetails.get("char1")!!.server)
        assertFalse(loginDetails.get("char1")!!.enabled)

        assertEquals(
            mapOf(
                "char1" to mapOf(
                    "username" to "username",
                    "password" to "password",
                    "server" to "light_in_the_darkness",
                    "enabled" to false,
                )
            ),
            LoginDetailsConfigLoader().toYaml(loginDetails),
        )
    }

    @Test
    fun `none not stringified`() {
        val config = Config(
            attack = AttackConfig(
                attacks = listOf(listOf(1, 1000)),
                bindings = LinkedHashMap(mapOf("battle_hp_pot" to "F1", "battle_mp_pot" to "F2")),
            )
        ).toYaml()

        for ((_, conf) in config) {
            val bindings = (conf as Map<*, *>)["bindings"] as? Map<*, *> ?: continue
            for (v in bindings.values) {
                assertTrue(v != "None", "binding value stringified to None: $v")
            }
        }
    }

    @Test
    fun `config file round trip`(@TempDir dir: Path) {
        val file = dir.resolve("char.yml").toString()
        val original = Config(
            attack = AttackConfig(
                attacks = listOf(listOf(1, 1000)),
                spot = 123 to 456,
                stuckInterval = 10,
            ),
            regen = RegenConfig(
                hpThreshold = 0.8,
                manaThreshold = 0.75,
            ),
        )
        original.validate()
        original.saveFile(file)
        val loaded = Config.loadFile(file)
        assertEquals(original, loaded)
        assertEquals(123 to 456, loaded.attack!!.spot as Pair<Int, Int>)
        assertEquals(0.8, loaded.regen!!.hpThreshold as Double)
    }

    @Test
    fun `load yaml from string`() {
        val yaml = """
            regen:
              hp_threshold: 0.9
              mana_threshold: 0.5
              bindings:
                sit: x
        """.trimIndent()
        val config = Config.loadYaml(yaml)
        assertEquals(0.9, config.regen!!.hpThreshold as Double)
        assertEquals("x", config.regen!!.bindingsMap()["sit"])
        assertEquals(listOf("regen"), config.functions())
    }
}
