package com.ghostbot.functions

import com.ghostbot.controller.BotClientWindow
import com.ghostbot.lib.seconds
import com.ghostbot.lib.sleepSeconds

/**
 * Port of GhostBot/functions/regen.py.
 */
class Regen(client: BotClientWindow, private val fairyActivated: Boolean = false) :
    Locational(client) {

    private val config = client.config?.regen ?: error("regen config required")
    private val manaThreshold: Double = (config.manaThreshold as? Double) ?: 0.75
    private val hpThreshold: Double = (config.hpThreshold as? Double) ?: 0.75

    override fun _run(): Boolean {
        // :return: true if we healed successfully, false if we were attacked
        // or in battle while healing
        if (manaLow() || hpLow()) {
            gotoStartLocation()

            val startWait = System.currentTimeMillis()
            if (client.inBattle) {
                var waitedOut = false
                while (client.inBattle && System.currentTimeMillis() - startWait < seconds(sec = 3) * 1000) {
                    sleepSeconds(0.5)
                    if (!client.inBattle) {
                        waitedOut = true
                        break
                    }
                }
                // Python while-else: loop ended by the 3s timeout (still in battle)
                if (!waitedOut && client.inBattle) return false
            }
            _logInfo("low hp/mana, starting Regen")

            val bindings = config.bindingsMap()
            if (bindings.isNotEmpty()) {
                // mana/hp pots
                useHpPot(bindings)
                useManaPot(bindings)
            }

            val currentHp = client.hp ?: return false
            var hp = currentHp
            val waitCondition: () -> Boolean = if (fairyActivated) {
                { (client.mana ?: 0) < (client.maxMana ?: 0) }
            } else {
                { (client.mana ?: 0) < (client.maxMana ?: 0) || (client.hp ?: 0) < (client.maxHp ?: 0) }
            }
            while (waitCondition() && client.running) {
                _logDebug("healing")
                sleepSeconds(2.0)
                if (client.inBattle || (client.hp ?: 0) < hp) {
                    _logDebug("Ouch, attacking")
                    return false
                }
                gotoSpotAndSit()
                hp = client.hp ?: return false
            }
            return true
        }
        return false
    }

    private fun manaLow(): Boolean = client.manaPercent() < manaThreshold

    private fun hpLow(): Boolean {
        if (fairyActivated) return false
        return client.hpPercent() < hpThreshold
    }

    private fun useHpPot(bindings: Map<String, Any?>) {
        if (client.hpPercent() < hpThreshold) {
            val key = bindings["hp_pot"]
            if (key != null) {
                gotoSpotAndSit()
                client.pressKey(key)
            }
        }
    }

    private fun useManaPot(bindings: Map<String, Any?>) {
        if (client.manaPercent() < manaThreshold) {
            val key = bindings["mana_pot"]
            if (key != null) {
                gotoSpotAndSit()
                client.pressKey(key)
            }
        }
    }

    private fun gotoSpotAndSit() {
        gotoStartLocation()
        sit()
    }

    private fun sit() {
        if (!client.sitting) {
            _logDebug("sitting")
            client.sit(config.bindingsMap()["sit"])
        }
    }
}
