package com.ghostbot.functions

import com.ghostbot.controller.BotClientWindow
import com.ghostbot.lib.linearDistance
import com.ghostbot.lib.sleepSeconds
import java.util.logging.Level

/**
 * Port of GhostBot/functions/runner.py.
 *
 * Python's `@run_at_interval` metaprogramming is expressed as three overridable
 * hooks on [Runner]: [isIntervalFunction], [intervalGate] and the
 * [lastTimeRan] bookkeeping, driven from [run].
 */

/**
 * Base mixin providing client-scoped logging, mirroring `InjectedLoggingMixin`.
 */
abstract class InjectedLoggingMixin(val client: BotClientWindow) {
    val logger = java.util.logging.Logger.getLogger("GhostBot.Runner")
    private val errorLoggers = mutableListOf<(String) -> Unit>()
    private val infoLoggers = mutableListOf<(String) -> Unit>()
    private val debugLoggers = mutableListOf<(String) -> Unit>()

    init {
        if (!javaClass.simpleName.endsWith("Context")) {
            _logDebug("initializing ${javaClass.simpleName}...")
        }
    }

    /** Port of `add_logger` — register an extra consumer for a level. */
    fun addLogger(logger: (String) -> Unit, level: Level = Level.INFO) {
        if (level.intValue() < Level.INFO.intValue()) debugLoggers.add(logger)
        if (level.intValue() < Level.SEVERE.intValue()) infoLoggers.add(logger)
        errorLoggers.add(logger)
    }

    protected fun _logErr(msg: String) {
        val m = "${client.name}: $msg"
        logger.log(Level.SEVERE, m)
        errorLoggers.forEach { it(m) }
    }

    protected fun _logInfo(msg: String) {
        val m = "${client.name}: $msg"
        logger.log(Level.INFO, m)
        infoLoggers.forEach { it(m) }
    }

    protected fun _logDebug(msg: String) {
        val m = "${client.name}: $msg"
        logger.log(Level.FINE, m)
        debugLoggers.forEach { it(m) }
    }
}

/**
 * Base class for any optional function to be run on the bot (attack, regen, ...).
 */
abstract class Runner(client: BotClientWindow) :
    InjectedLoggingMixin(client) {

    /** Port of the `@run_at_interval(run_on_start, run_in_battle)` bookkeeping. */
    protected var lastTimeRan: Long = if (runOnStart) 0 else System.currentTimeMillis()
    protected open val runOnStart: Boolean get() = false
    protected open val runInBattle: Boolean get() = false
    /** Interval in ms; null for non-interval functions (run every tick). */
    protected open val intervalMs: Long? get() = null

    /** Non-interval functions: always eligible. Interval functions: gate on battle/interval. */
    protected open fun intervalGate(): Boolean {
        val interval = intervalMs
        if (interval == null) return true
        if (!runInBattle && client.inBattle) return false
        return System.currentTimeMillis() - lastTimeRan > interval
    }

    fun run() {
        if (client.botStatus != com.ghostbot.enums.BotStatus.RUNNING) {
            _logDebug("not running as client not in running status.")
            return
        }
        if (!intervalGate()) return
        val interval = intervalMs
        if (interval != null) lastTimeRan = System.currentTimeMillis()
        _run()
    }

    /** Port of `_run` — returns True when the function did meaningful work. */
    protected abstract fun _run(): Boolean?
}

/**
 * A function that has a concept of a home/start location.
 */
abstract class Locational(client: BotClientWindow) :
    Runner(client) {

    val startLocation: Pair<Int, Int> = determineStartLocation()

    /** Returns the config attack/fairy spot, or the char's current location. */
    protected open fun determineStartLocation(): Pair<Int, Int> {
        val attack = client.config?.attack
        attack?.let {
            it.spot?.let { s -> return s as Pair<Int, Int> }
        }
        val fairy = client.config?.fairy
        fairy?.let {
            it.spot?.let { s -> return s as Pair<Int, Int> }
        }
        return client.location.x to client.location.y
    }

    /** Moves the char to the saved start location. */
    protected fun gotoStartLocation() {
        while (linearDistance(startLocation, client.location.x to client.location.y) > 2 && client.running) {
            _logDebug("${client.name}: go to saved spot: $startLocation")
            client.moveToPos(startLocation)
        }
    }
}
