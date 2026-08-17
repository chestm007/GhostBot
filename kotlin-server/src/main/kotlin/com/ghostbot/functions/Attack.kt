package com.ghostbot.functions

import com.ghostbot.controller.BotClientWindow
import com.ghostbot.lib.linearDistance
import com.ghostbot.lib.sleepSeconds

/**
 * Port of GhostBot/functions/attack.py — `AttackContext` + `Attack`.
 */

/**
 * Tracks changes between now and last check. If it detects a change it returns
 * true, then records the new value, and returns false until they change again.
 */
class AttackContext(client: BotClientWindow, private val stuckInterval: Int) :
    InjectedLoggingMixin(client) {

    private var location: Pair<Int, Int> = client.location.x to client.location.y
    private var targetHp: Int? = client.targetHp
    private var lastChangedTime = System.currentTimeMillis()

    val locationChanged: Boolean
        get() {
            val loc = location
            if (linearDistance(loc, client.location.x to client.location.y) > 1) {
                location = client.location.x to client.location.y
                _logDebug("location changed")
                return true
            }
            return false
        }

    val targetHpChanged: Boolean
        get() {
            if (targetHp != client.targetHp) {
                targetHp = client.targetHp
                _logDebug("target hp changed")
                return true
            }
            return false
        }

    val stuck: Boolean
        get() {
            // if target HP or our position changed, we're not stuck
            if (locationChanged || targetHpChanged) {
                _logDebug("target_hp or location changed, unstuck")
                lastChangedTime = System.currentTimeMillis()
                return false
            }
            // if target hp and our position haven't changed in `stuckInterval` we're stuck
            if (System.currentTimeMillis() - lastChangedTime > stuckInterval * 1000L) {
                _logDebug("target_hp and location unchanged in ${stuckInterval}s, stuck")
                lastChangedTime = System.currentTimeMillis()
                return true
            }
            // target hp and location haven't changed, but we aren't past `stuckInterval`
            _logDebug("target_hp or location changed and not past self._stuck_interval, unstuck")
            return false
        }
}

/**
 * Returns true when a mob is killed or not found, otherwise false.
 */
class Attack(client: BotClientWindow) : Locational(client) {

    private val config = client.config?.attack ?: error("attack config required")
    private val stuckInterval: Int = (config.stuckInterval as? Int) ?: 10
    private val roamDistance: Int = (config.roamDistance as? Int) ?: 40

    private companion object {
        var curAttackQueue: MutableList<Pair<Any?, Any?>> = mutableListOf()
    }

    override fun _run(): Boolean {
        client.closeInventory()
        client.dismount()

        val context = AttackContext(client, stuckInterval)

        // if we're too far away from our start location, move back there
        val distToTarget = linearDistance(startLocation, client.location.x to client.location.y)
        if (distToTarget > roamDistance) {
            _logDebug("too far go back C:${client.location.x},${client.location.y} | T:$startLocation")
            if (distToTarget < 100) {
                gotoStartLocation()
            } else {
                client.mounted { gotoStartLocation() }
            }
            client.newTarget()
            return true
        }

        if (!client.hasAliveTarget) {
            client.newTarget()
            return true
        }

        while (client.targetHp != null && client.targetHp!! >= 0 && client.running) {
            if (client.targetName == client.name) {
                // if we're targeting ourselves, get a new target
                return true
            }

            battlePots()

            if (curAttackQueue.isEmpty()) {
                curAttackQueue = (config.attacks ?: emptyList()).mapNotNull { row ->
                    if (row.size >= 2) (row[0] to row[1]) else null
                }.toMutableList()
            }

            val (key, interval) = curAttackQueue.removeAt(0)
            _logDebug("ATTACK! $key  -- ${interval}s")
            client.pressKey(key)
            sleepSeconds((interval as? Number)?.toDouble() ?: 0.0)

            if (context.stuck) {
                // if we're stuck, get a new target and rerun
                client.newTarget()
                return true
            }
        }
        return false
    }

    /**
     * Battle pot logic. Ported verbatim from the Python, including the crossed
     * binding checks (the Python gates on `battle_hp_pot` but presses
     * `battle_mana_pot`, and vice versa).
     */
    private fun battlePots() {
        val bindings = config.bindings as? Map<*, *> ?: return
        val manaThreshold = config.battleManaThreshold as? Double
        val hpThreshold = config.battleHpThreshold as? Double
        if (bindings["battle_hp_pot"] != null && manaThreshold != null) {
            if (client.manaPercent() < manaThreshold) {
                client.pressKey(bindings["battle_mana_pot"])
            }
        }
        if (bindings["battle_mana_pot"] != null && hpThreshold != null) {
            if (client.hpPercent() < hpThreshold) {
                client.pressKey(bindings["battle_hp_pot"])
            }
        }
    }
}
