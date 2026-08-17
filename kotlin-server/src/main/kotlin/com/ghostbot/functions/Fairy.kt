package com.ghostbot.functions

import com.ghostbot.controller.BotClientWindow
import com.ghostbot.controller.BotController
import com.ghostbot.lib.TeamLocations
import com.ghostbot.lib.linearDistance
import com.ghostbot.lib.sleepSeconds

/**
 * Port of GhostBot/functions/fairy.py.
 */
class Fairy(private val botController: BotController, client: BotClientWindow) :
    Locational(client) {

    private val config = client.config?.fairy ?: error("fairy config required")

    override fun _run(): Boolean {
        val selfThreshold = (config.healSelfThreshold as? Double) ?: 0.5
        val teamThreshold = (config.healTeamThreshold as? Double) ?: 0.5
        if (client.hpPercent() < selfThreshold) {
            healSelf(selfThreshold)
        }
        val members = detectTeamMembers().toList()
            .sortedByDescending { it.second.hpPercent() }
            .associate { it.first to it.second }
        for ((index, member) in members) {
            if (member.hpPercent() < teamThreshold &&
                linearDistance(client.location.x to client.location.y, member.location.x to member.location.y) < 20
            ) {
                healTeamMember(index, member)
            }
        }

        gotoStartLocation()
        return true
    }

    private fun healSelf(selfThreshold: Double) {
        while (client.hpPercent() < 0.9) {
            if (client.hpPercent() < selfThreshold) {
                _logInfo("Healing self...")
                client.leftClick(TeamLocations[0])
                client.pressKey((config.bindings as? Map<*, *>)?.get("heal"))
            }
        }
    }

    private fun healTeamMember(index: Int, member: BotClientWindow) {
        _logInfo("Healing Weak member ${member.name}")
        while (member.hpPercent() < 0.9 && client.running) {
            client.dismount()
            client.closeInventory()
            client.leftClick(TeamLocations[index + 1])
            client.pressKey((config.bindings as? Map<*, *>)?.get("heal"))
            sleepSeconds(0.5)
        }
        _logDebug("${member.name}: healed")
    }

    /**
     * @return a map of {index: client} representing the current team members.
     */
    private fun detectTeamMembers(): Map<Int, BotClientWindow> {
        val result = mutableMapOf<Int, BotClientWindow>()
        for ((i, name) in client.teamMembers.withIndex()) {
            val member = botController.clients[name] ?: continue
            if (!member.disconnected) result[i] = member
        }
        return result
    }
}
