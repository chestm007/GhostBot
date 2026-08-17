package com.ghostbot.functions

import com.ghostbot.controller.BotClientWindow
import com.ghostbot.lib.seconds
import com.ghostbot.lib.sleepSeconds

/**
 * Port of GhostBot/functions/buffs.py — `@run_at_interval(run_on_start=True)`.
 */
class Buffs(client: BotClientWindow) : Runner(client) {

    private val config = client.config?.buff ?: error("buff config required")

    override val runOnStart: Boolean get() = true
    override val intervalMs: Long = seconds(minutes = (config.interval as? Int) ?: 10).toLong() * 1000

    override fun _run(): Boolean {
        _logInfo("Buffing.")
        for (row in config.buffs ?: emptyList()) {
            if (row.size < 2) continue
            client.pressKey(row[0])
            sleepSeconds(((row[1] as? Number)?.toDouble() ?: 0.0) / 1000.0)
        }
        return true
    }
}
