package com.ghostbot.functions

import com.ghostbot.controller.BotClientWindow
import com.ghostbot.lib.seconds
import com.ghostbot.lib.sleepSeconds

/**
 * Port of GhostBot/functions/petfood.py — `@run_at_interval()`.
 */
class Petfood(client: BotClientWindow) : Runner(client) {

    companion object {
        const val COMMAND_DELAY = 5.0
    }

    private val config = client.config?.pet ?: error("pet config required")
    override val intervalMs: Long = seconds(minutes = (config.foodIntervalMins as? Int) ?: 0).toLong() * 1000

    private var lastTimePetSpawned = 0L

    init {
        // Python `@run_at_interval` calls `_setup` right after init.
        spawnPet()
    }

    private val spawnPetHotkey: Any?
        get() {
            _logDebug("spawn_pet_hotkey: ${(config.bindings as? Map<*, *>)?.get("spawn")}")
            return (config.bindings as? Map<*, *>)?.get("spawn")
        }

    override fun _run(): Boolean {
        client.dismount()
        feedPet()
        respawnPet()
        return true
    }

    private fun feedPet() {
        _logInfo("Feeding pet")
        client.pressKey((config.bindings as? Map<*, *>)?.get("food"))
        sleepSeconds(COMMAND_DELAY)
    }

    private fun despawnPet() {
        while (client.petActive && client.running) {
            _logInfo("Despawning pet")
            client.pressKey(spawnPetHotkey)
            var poll = 0
            while (client.petActive && client.running && poll < 10) {
                poll++
                sleepSeconds(0.5)
            }
        }
    }

    private fun spawnPet() {
        while (!client.petActive && client.running) {
            _logInfo("Spawning pet")
            client.pressKey(spawnPetHotkey)
            var poll = 0
            while (!client.petActive && client.running && poll < 10) {
                poll++
                sleepSeconds(0.5)
            }
        }
    }

    private fun respawnPet() {
        val spawnInterval = (config.spawnIntervalMins as? Int) ?: 0
        if (System.currentTimeMillis() - lastTimePetSpawned > seconds(minutes = spawnInterval) * 1000) {
            despawnPet()
            spawnPet()
            lastTimePetSpawned = System.currentTimeMillis()
        }
    }
}
