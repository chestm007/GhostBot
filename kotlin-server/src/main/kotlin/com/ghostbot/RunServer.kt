package com.ghostbot

import com.ghostbot.controller.ThreadedBotController

/**
 * Port of GhostBot/run_server.py.
 *
 * ```
 * mvn -q exec:java   # or: java -jar ghostbot-server.jar
 * ```
 */
fun main() {
    // Mirror of the PYCHARM_HOSTED debug hook.
    if (System.getenv("PYCHARM_HOSTED") != null) {
        java.util.logging.Logger.getLogger("GhostBot").level = java.util.logging.Level.FINE
    }

    configureLogging()

    val botController = ThreadedBotController()
    try {
        botController.listen()
    } catch (e: InterruptedException) {
        rootLogger.info("received signal, exiting")
    } finally {
        rootLogger.info("exiting...")
        botController.shutdown()
    }
}
