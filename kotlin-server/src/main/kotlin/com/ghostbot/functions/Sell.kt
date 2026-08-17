package com.ghostbot.functions

import com.ghostbot.controller.BotClientWindow
import com.ghostbot.lib.UILocations
import com.ghostbot.lib.itemCoordinatesFromPos
import com.ghostbot.lib.linearDistance
import com.ghostbot.lib.seconds
import com.ghostbot.lib.sleepSeconds

/**
 * Port of GhostBot/functions/sell.py.
 */
class Sell(client: BotClientWindow) : Locational(client) {

    private val config = client.config?.sell ?: error("sell config required")
    override val intervalMs: Long = seconds(minutes = (config.sellIntervalMins as? Int) ?: 60).toLong() * 1000
    private val returnSpot: Pair<Int, Int>? = determineStartLocation()

    private val useMount: Boolean
    private val mountKey: Any?
    private val sellNpcName: String?
    private val sellItemPos: Int

    private var lastTimeSold = 0L

    init {
        val bindings = config.bindings as? Map<*, *>
        useMount = (config.useMount as? Boolean) ?: false
        mountKey = bindings?.get("mount")
        if (bindings == null) {
            _logDebug("No mount key set, self._use_mount = False")
        }
        sellNpcName = config.sellNpcName
        sellItemPos = (config.sellItemPos as? Int) ?: 1
        if (config.npcSellClickSpot == null) {
            _logErr("NPC sell click spot not set")
        }
    }

    override fun _run(): Boolean {
        client.mounted(mountKey) {
            if (!goToNpc()) {
                return@mounted false
            }

            sleepSeconds(2.0)
            sellItems()

            sleepSeconds(2.0)
            pathToAttackSpot()

            return@mounted true
        }
        return false
    }

    private fun goToNpc(): Boolean {
        pathToNpcSearchSpot()
        client.searchSurroundings(sellNpcName ?: "")
        try {
            val firstResult = client.pointers?.getSurInfo()
            if (sellNpcName != null && firstResult != null &&
                sellNpcName in firstResult["name"].orEmpty()
            ) {
                val coords = firstResult["coords"]!!.split(",")
                val npcLocation = coords[0].toInt() to coords[1].toInt()
                client.gotoFirstSurroundingResult()
                _logInfo("Going to npc location $npcLocation")
                while (linearDistance(client.location.x to client.location.y, npcLocation) > 2 && client.running) {
                    sleepSeconds(0.5)
                }
            } else {
                _logInfo("No npc location found")
            }
        } catch (e: Exception) {
            _logInfo("Memory access failed to get npc location, falling back to movement detection :(")
            client.gotoFirstSurroundingResult()
            sleepSeconds(5.0)
            client.blockWhileMoving()
        }
        return true
    }

    private fun sellItems() {
        _logInfo("Selling...")
        client.resetCamera()
        sleepSeconds(2.0)
        client.clickNpc()
        sleepSeconds(1.0)
        val spot = config.npcSellClickSpot as? Pair<Int, Int> ?: return
        client.leftClick(spot)
        sleepSeconds(1.0)
        repeat(24) {
            client.leftClick(itemCoordinatesFromPos(sellItemPos, UILocations.sellItemSlot1))
        }
        client.leftClick(UILocations.confirmSellButton)
    }

    private fun pathToNpcSearchSpot() {
        val spot = config.npcSearchSpot as? Pair<Int, Int>
        if (spot != null) {
            _logInfo("going to npc search location $spot")
            client.moveToPos(spot)
        }
    }

    private fun pathToAttackSpot() {
        if (returnSpot != null) {
            _logInfo("returning to $returnSpot")
            // TODO: loop trying to move via map until the char moves.
            client.moveToPos(returnSpot)
            gotoStartLocation()
        }
    }
}
