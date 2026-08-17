package com.ghostbot.functions

import com.ghostbot.ImageFinder
import com.ghostbot.controller.BotClientWindow
import com.ghostbot.lib.seconds
import com.ghostbot.lib.sleepSeconds

/**
 * Port of GhostBot/functions/delete.py — `@run_at_interval(run_on_start=True)`.
 */
class Delete(client: BotClientWindow) : Runner(client) {

    private val imageFinder = ImageFinder(client)

    override val runOnStart: Boolean get() = true
    override val intervalMs: Long =
        seconds(minutes = (client.config?.delete?.interval as? Int) ?: 10).toLong() * 1000
    private val deleteTrash: Boolean =
        (client.config?.delete?.deleteTrash as? Boolean) ?: false

    init {
        // The Python prints dialog_ok_location here (an image-discovery side effect).
        _logDebug("dialog_ok_location: ${imageFinder.dialogOkLocation}")
    }

    override fun _run(): Boolean {
        _logInfo("running delete function")

        if (deleteTrash) {
            _logInfo("Deleting trash")
            runDeleteTrash()
        }
        return true
    }

    private fun runDeleteTrash() {
        client.inventory {
            for (itemPos in imageFinder.findItemsInWindow(ImageFinder.items)) {
                client.leftClick(itemPos)
                val destroyPos = imageFinder.destroyItemLocation
                if (destroyPos != null) client.leftClick(destroyPos)
                sleepSeconds(0.3)
                val okPos = imageFinder.dialogOkLocation
                if (okPos != null) {
                    client.leftClick(okPos)
                }
            }
        }
    }
}
