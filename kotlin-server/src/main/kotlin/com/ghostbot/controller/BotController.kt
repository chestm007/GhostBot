package com.ghostbot.controller

import com.ghostbot.Win32ClientWindow
import com.ghostbot.config.Config
import com.ghostbot.config.ConfigLoader
import com.ghostbot.config.GhostBotServerConfigLoader
import com.ghostbot.config.LoginDetailsConfigLoader
import com.ghostbot.enums.BotStatus
import com.ghostbot.functions.Attack
import com.ghostbot.functions.Buffs
import com.ghostbot.functions.Delete
import com.ghostbot.functions.Fairy
import com.ghostbot.functions.Petfood
import com.ghostbot.functions.Regen
import com.ghostbot.functions.Runner
import com.ghostbot.functions.Sell
import com.ghostbot.ipc.IpcServer
import com.ghostbot.ipc.IpcServerLogHandler
import com.ghostbot.ipc.Message
import com.ghostbot.lib.UILocations
import com.ghostbot.lib.coordsToMapScreenPos
import com.ghostbot.lib.linearDistance
import com.ghostbot.lib.positionDifference
import com.ghostbot.lib.scaleMinimapMoveDistance
import com.ghostbot.lib.sleepSeconds
import com.ghostbot.mapNavigation.locationToZoneMap
import com.ghostbot.mapNavigation.zones
import com.ghostbot.rootLogger
import com.ghostbot.server.GhostbotIpcServer
import com.ghostbot.win32.ProcessMemory
import java.util.concurrent.locks.ReentrantLock
import java.util.logging.Level
import kotlin.math.ceil

/**
 * Port of GhostBot/controller/bot_controller.py.
 */

private val lock = ReentrantLock()

class BotClientWindow(proc: ProcessMemory) : Win32ClientWindow(proc) {
    var running: Boolean = false
    var botStatus: BotStatus = BotStatus.CREATED
    var config: Config? = null

    init {
        if (disconnected) {
            botStatus = BotStatus.DISCONNECTED
        }
        loadConfig()
    }

    /** Port of `BotClientWindow.to_json` — state for the INFO_CHAR command. */
    fun toJson(): Map<String, Any?> {
        val pointers = pointers
        return linkedMapOf(
            "name" to name,
            "status" to botStatus.name,
            "hp" to hp,
            "mana" to mana,
            "max_hp" to maxHp,
            "max_mana" to maxMana,
            "level" to level,
            "target_name" to targetName,
            "target_hp" to targetHp,
            "location_x" to location.x,
            "location_y" to location.y,
            "location_name" to locationName,
            "pet_active" to petActive,
            "sitting" to sitting,
            "in_battle" to inBattle,
            "inventory_open" to inventoryOpen,
            "mounted" to onMount,
            "window_pos" to getWindowPos()?.let { "${it.x}, ${it.y}" },
            "window_size" to getWindowSize()?.let { "${it.x}, ${it.y}" },
            "notification" to notification,
            "confirm" to pointers?.confirmBox(),
            "dialog" to pointers?.getDialog(),
            "dc" to pointers?.getDc(),
        )
    }

    override fun postLoginSetup() {
        super.postLoginSetup()
        botStatus = BotStatus.CREATED
        loadConfig()
    }

    override fun mount(key: Any?) {
        val c = config
        val sell = c?.sell
        if (c != null && sell != null && (sell.useMount as? Boolean) == true) {
            super.mount(key)
        }
    }

    fun unmount(key: Any?) {
        val c = config
        val sell = c?.sell
        if (c != null && sell != null && (sell.useMount as? Boolean) == true) {
            dismount(key)
        }
    }

    fun loadConfig() {
        applyConfig(ConfigLoader(name ?: "unknown").load())
    }

    fun applyConfig(config: Config) {
        this.config = config
    }

    val botStatusString: String get() = botStatus.name

    override val disconnected: Boolean
        get() {
            if (super.disconnected) {
                botStatus = BotStatus.DISCONNECTED
                return true
            }
            return false
        }

    override fun hpPercent(): Double = (hp ?: 0).toDouble() / (maxHp ?: 0)

    override fun manaPercent(): Double = (mana ?: 0).toDouble() / (maxMana ?: 0)

    fun startBot() {
        logger.info("${name}: Starting...")
        if (disconnected) {
            botStatus = BotStatus.DISCONNECTED
            logger.info("${name}: Client disconnected.")
        }
        botStatus = BotStatus.STARTING
        running = true
        loadConfig()
    }

    fun stopBot() {
        logger.info("${name}: Stopping...")
        botStatus = BotStatus.STOPPING
        running = false
    }

    /**
     * Moves to [targetPos], invoking map-based pathing if the distance is too far.
     */
    fun moveToPos(targetPos: Pair<Int, Int>) {
        while (linearDistance(location.x to location.y, targetPos) > 50 && running) {
            logger.log(Level.FINE, "${name} moving via map")
            moveToPosViaMap(targetPos)
            return
        }

        val posDiff = positionDifference(
            location.x.toDouble() to location.y.toDouble(),
            targetPos.first.toDouble() to targetPos.second.toDouble()
        )

        // corrected to represent 1 pixel per meter
        val posDiffMmPix = (-1.7 * posDiff.first) to (1.7 * posDiff.second)

        val minimapRelativePos = scaleMinimapMoveDistance(posDiffMmPix)
        val minimapPos = (ceil((UILocations.minimapCentre.first + minimapRelativePos.first).toDouble()).toInt()
            to ceil((UILocations.minimapCentre.second + minimapRelativePos.second).toDouble()).toInt())

        logger.log(Level.FINE, "${name}: clicking $minimapRelativePos") // relative to minimap center
        rightClick(minimapPos)
        blockWhileMoving()
    }

    private fun moveToPosViaMap(targetPos: Pair<Int, Int>): Boolean {
        val zoneName = locationToZoneMap[locationName?.trim() ?: ""]
            ?: run {
                logger.severe("no zone for location ${locationName}")
                return false
            }
        val zone = zones.getValue(zoneName)
        val screenCoords = coordsToMapScreenPos(
            zone,
            targetPos.first.toDouble() to targetPos.second.toDouble()
        )
        // Open the map, and try a list of position offsets, starting at the exact
        // point we want to go to — this avoids movement being blocked when team
        // members are already where we want to be.
        val offsets = listOf(
            0 to 0, 20 to 0, -20 to 0, 20 to 20, -20 to 20, -20 to -20, 0 to -20, -20 to 20, 0 to 20,
        )
        var pathTgt = screenCoords
        openMap()
        try {
            sleepSeconds(1.0)
            val loc = location
            // Click away from tgt to clear possible existing tgt
            rightClick(screenCoords.first - 30 to screenCoords.second - 30)
            var moved = false
            for ((dx, dy) in offsets) {
                pathTgt = (screenCoords.first + dx) to (screenCoords.second + dy)
                rightClick(pathTgt)
                sleepSeconds(2.0)
                if (linearDistance(loc.x to loc.y, location.x to location.y) > 1) {
                    // If we've started moving, we can stop trying offsets
                    moved = true
                    break
                }
            }
            if (!moved) {
                logger.info("${name}: failed pathing via map")
                return false
            }
        } finally {
            closeMap()
        }

        blockWhileMoving(pathTgt)
        if (targetPos != pathTgt) {
            // If we moved to a non-zero offset location, we need to use the
            // minimap to move to the right spot — close enough now that it'll work.
            moveToPos(targetPos)
            blockWhileMoving()
        }
        return true
    }

    /**
     * Blocks until the char stops moving (or gets close enough to [destination]).
     */
    fun blockWhileMoving(destination: Pair<Int, Int>? = null) {
        while (running) {
            val loc = location
            sleepSeconds(1.0)
            if (destination != null) {
                if (linearDistance(destination, location.x to location.y) < 40) {
                    // if we're close enough, no point overshooting
                    logger.log(Level.FINE, "block_while_moving: unblocking due to proximity")
                    break
                }
            }
            if (linearDistance(location.x to location.y, loc.x to loc.y) < 1) {
                logger.log(Level.FINE, "block_while_moving: unblocking due to no movement")
                break
            }
        }
    }
}

/**
 * Base bot controller — owns the IPC server, the client registry and login config.
 */
abstract class BotController(
    host: String? = null,
    port: Int? = null,
    private val closeDisconnectedClients: Boolean = true,
) {
    val server: GhostbotIpcServer = GhostbotIpcServer(this, host ?: "localhost", port ?: 64057)
    val ipcLogHandler = IpcServerLogHandler(server)
    val logger = java.util.logging.Logger.getLogger("GhostBot.BotController")

    @Volatile
    protected var _running: Boolean = false
    protected var controllerStartTime = System.currentTimeMillis()

    val clients = LinkedHashMap<String, BotClientWindow>()
    val pendingClients = LinkedHashMap<String, BotClientWindow>()
    val loginQueue = LinkedHashMap<Int, BotClientWindow>()
    val requestedLogins = mutableListOf<String>()
    var loginConfig: LoginDetailsConfigLoader.LoginDetails? = null
        protected set
    private var seenClients: List<Int> = emptyList()

    init {
        logger.addHandler(ipcLogHandler)
        GhostBotServerConfigLoader().load()
        loadLoginConfig()
    }

    val running: Boolean get() = _running

    protected val totalRunningSecs: Int
        get() = ((System.currentTimeMillis() - controllerStartTime) / 1000).toInt()

    protected fun loadLoginConfig() {
        loginConfig = LoginDetailsConfigLoader().load()
    }

    /** Port of `_eligible_logins`. */
    protected fun eligibleLogins(): LinkedHashMap<String, LoginDetailsConfigLoader.CharDetails> {
        lock.lock()
        try {
            val result = LinkedHashMap<String, LoginDetailsConfigLoader.CharDetails>()
            val loggedInClients = clientKeys + pendingClients.keys
            for ((k, v) in loginConfig?.chars.orEmpty()) {
                if (k !in loggedInClients) {
                    if (k in requestedLogins || v.enabled) {
                        result[k] = v
                    }
                }
            }
            return result
        } finally {
            lock.unlock()
        }
    }

    /** Port of `_scan_for_clients`. */
    protected open fun scanForClients() {
        val currentRunningProcs = ProcessMemory.listClients()

        // remove_closed_clients
        lock.lock()
        try {
            for (v in clients.values.toList()) {
                val cPid = v.processId
                if (cPid !in currentRunningProcs.map { it.processId }) {
                    logger.log(Level.INFO, "removing [$cPid]")
                    try {
                        val removed = removeClient(v, close = closeDisconnectedClients)
                        stopBot(removed, 5)
                    } catch (e: Exception) {
                        logger.log(Level.SEVERE, "error removing client", e)
                    }
                }
            }
        } finally {
            lock.unlock()
        }

        val currentClientProcIds = clients.values.map { it.processId }.toSet()

        val procIds = currentRunningProcs.map { it.processId }
        if (procIds == seenClients) {
            logger.log(Level.FINE, "No change in running processes")
            seenClients = procIds
            return
        }
        seenClients = procIds

        for (proc in currentRunningProcs) {
            if (proc.processId in currentClientProcIds) {
                logger.log(Level.FINE, "Process [${proc.processId}] already registered with BotController, skipping.")
                continue
            }
            val client = BotClientWindow(proc)
            try {
                if (client.name == null && client.getWindowName() !in pendingClients.keys) {
                    logger.log(Level.FINE, "[${proc.processId}] client.name is None, possibly hasnt logged in yet")
                    if (proc.processId !in loginQueue.keys) {
                        logger.info("[${proc.processId}] adding process to login_queue routine")
                        loginQueue[proc.processId] = client
                    }
                    continue
                }
                val level = client.level
                // Note: the Python checks `0 > client.level >= 89` which is a
                // no-op (chained comparison can never be true); the clear intent
                // — and the log message — is "skip out-of-range levels".
                if (level == null || level < 0 || level > 89) {
                    logger.info("[${proc.processId}] client.level($level) < 0 or > 89.")
                    continue
                }

                if (client.disconnected) {
                    logger.info("Detected disconnected client window for char [${client.name}], attempting to restart")
                    removeClient(client, close = closeDisconnectedClients)
                    sleepSeconds(0.5)
                } else {
                    if (client.name !in clientKeys) {
                        logger.info("adding client ${client.name} ${client.disconnected}")
                        addClient(BotClientWindow(proc))
                    } else {
                        logger.log(Level.FINE, "client ${client.identifier} already exists, skipping")
                    }
                }
            } catch (e: Exception) {
                // TypeError/AttributeError in the Python
                logger.info("cannot add client $proc")
            }
        }
    }

    val clientKeys: List<String>
        get() = clients.keys.map { it.toString() }

    fun addClient(client: BotClientWindow): BotClientWindow {
        lock.lock()
        try {
            client.name?.let { clients[it] = client }
            server.sendToAll(server.botControllerClientsMessage)
        } finally {
            lock.unlock()
        }
        return client
    }

    fun removeClient(client: BotClientWindow, close: Boolean = true): BotClientWindow {
        try {
            val name = client.name
            if (name != null) {
                clients.remove(name)
                server.sendToAll(server.botControllerClientsMessage)
            }
        } catch (e: Exception) {
            logger.info(
                "client window for char ${client.identifier} not in registered clients list, " +
                    "this is normal if this is a fresh restart of the bot controller"
            )
        }
        if (close) {
            logger.info("client window for char ${client.identifier} will be closed")
            client.closeWindow()
        }
        return client
    }

    abstract fun startBot(client: BotClientWindow)

    abstract fun stopBot(client: BotClientWindow, timeout: Int = 5)

    abstract fun stopAllBots(timeout: Int = 30)

    abstract fun listen()

    fun reloadBotConfig(client: BotClientWindow) {
        client.loadConfig()
    }

    fun getClient(name: String?): BotClientWindow? {
        val client = clients[name]
        if (client == null) {
            logger.warning("no client $name")
        }
        return client
    }

    /** Port of `_get_functions_for_client`. */
    protected fun getFunctionsForClient(client: BotClientWindow): List<Runner> {
        val functions = mutableListOf<Runner>()
        client.config?.delete?.let { functions.add(Delete(client)) }
        client.config?.sell?.let { functions.add(Sell(client)) }
        client.config?.pet?.let { functions.add(Petfood(client)) }
        client.config?.regen?.let { functions.add(Regen(client, client.config?.fairy != null)) }
        client.config?.buff?.let { functions.add(Buffs(client)) }
        client.config?.attack?.let { functions.add(Attack(client)) }
        client.config?.fairy?.let { functions.add(Fairy(this, client)) }
        return functions
    }

    open fun shutdown() {
        _running = false
        stopAllBots(5)
    }
}
