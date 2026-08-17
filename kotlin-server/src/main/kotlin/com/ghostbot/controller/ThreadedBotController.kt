package com.ghostbot.controller

import com.ghostbot.ClientLauncher
import com.ghostbot.config.LoginDetailsConfigLoader
import com.ghostbot.enums.BotStatus
import com.ghostbot.lib.sleepSeconds
import com.ghostbot.win32.ProcessMemory
import java.util.logging.Level

/**
 * Port of GhostBot/controller/threaded_bot_controller.py.
 */
class ThreadedBotController(
    val autoLogin: Boolean = true,
    host: String? = null,
    port: Int? = null,
    closeDisconnectedClients: Boolean = true,
) : BotController(host, port, closeDisconnectedClients) {

    private val tasks = LinkedHashMap<String, Thread>()

    override fun scanForClients() {
        try {
            while (_running) {
                  logger.log(Level.FINE, "uptime ${totalRunningSecs}s")
                try {
                    removeClosedPendingClients()
                    super.scanForClients()

                    if (autoLogin) {
                        processLoginQueue()
                    }
                } catch (e: java.lang.UnsatisfiedLinkError) {
                    // Win32 process enumeration (kernel32/user32 via JNA) only
                    // exists on Windows. An UnsatisfiedLinkError is an Error, not
                    // an Exception, so it would otherwise kill this thread
                    // silently. Stop the scan loop; the IPC server keeps serving.
                    logger.log(
                        Level.SEVERE,
                        "Win32 process enumeration is not available on this OS " +
                            "(${e.message}); scan loop disabled, IPC server continues."
                    )
                    break
                }

                for (i in 0 until 10) {
                    if (!_running) break
                    sleepSeconds(1.0)
                }
            }
        } catch (e: InterruptedException) {
            logger.info("Exiting as requested...")
        } catch (e: Exception) {
            logger.log(Level.SEVERE, "scan loop error", e)
        }
    }

    private fun processLoginQueue() {
        val callback = { client: BotClientWindow, result: Boolean ->
            if (!result) {
                logger.log(
                    Level.FINE,
                    "[${client.processId}] Login failed, removing ${client.name} from self._pending_clients"
                )
                runCatching { pendingClients.remove(client.name) }
                    .onFailure {
                        logger.log(Level.FINE, "[${client.name}] pending client not found.. possibly harmless")
                    }
            } else {
                logger.log(Level.FINE, "[${client.processId}] :: Login succeeded")
                pendingClients.remove(client.name)
                addClient(client)
            }
        }

        val eligibleLogins = eligibleLogins()

        if (eligibleLogins.isEmpty()) {
            logger.log(Level.FINE, "no eligible logins...")
            return
        } else if (loginQueue.size < 1) {
            try {
                if (ProcessMemory.getProcMatching("game.exe").isEmpty()) {
                    logger.log(Level.FINE, "spawning game launcher")
                    ClientLauncher().blockUntilReady()
                } else {
                    logger.log(Level.FINE, "game launcher already running")
                }
            } catch (e: NoSuchElementException) {
                logger.log(Level.FINE, "game launcher process didnt launch, retrying")
            } catch (e: Exception) {
                logger.log(Level.FINE, "too many game launcher processes detected, there can only be one")
            }
        }

        for ((pid, client) in LinkedHashMap(loginQueue)) {
            if ("task$pid" in tasks.keys) continue

            val lc = LoginController(client, this)

            if (lc.currentStage == LoginController.LoginStage.CHARACTER_SELECT) {
                // fixes a race condition with the client window opening
                sleepSeconds(5.0)
            }
            val windowChar = client.getWindowName()

            logger.log(Level.FINE, "self._eligible_logins :: $eligibleLogins")

            var conf: LoginDetailsConfigLoader.CharDetails? = null
            when {
                windowChar in eligibleLogins && client.name == null -> {
                    conf = eligibleLogins.remove(windowChar)
                    logger.info("[$pid|${conf?.charName}] resuming login procedure with config $conf")
                }
                lc.currentStage == LoginController.LoginStage.ENTER_CREDENTIALS -> {
                    if (eligibleLogins.isEmpty()) {
                        logger.warning("[$pid|$windowChar] no eligible logins left for enter_credentials stage, skipping")
                        continue
                    }
                    val (key, value) = eligibleLogins.entries.first()
                    eligibleLogins.remove(key)
                    conf = value
                    logger.info("[$pid|${conf.charName}] starting login procedure with config $conf")
                }
                else -> {
                    logger.info("[$pid|$windowChar] skipping")
                    continue
                }
            }
            val selected = conf!!
            if (selected.charName in requestedLogins) {
                requestedLogins.remove(selected.charName)
            }

            pendingClients[selected.charName] = client

            logger.log(Level.FINE, "LoginStage of new pending client :: ${lc.currentStage}")

            logger.log(Level.FINE, "[$pid|${selected.charName}] setting config for LoginController")
            lc.setConfig(selected)
            addTask({ lc.handleLogin { result -> callback(client, result) } }, "task$pid")
            loginQueue.remove(pid)
        }
    }

    private fun removeClosedPendingClients() {
        val currentRunningProcs = ProcessMemory.listClients()
        for ((k, v) in LinkedHashMap(pendingClients)) {
            val cPid = v.processId
            if (cPid !in currentRunningProcs.map { it.processId }) {
                logger.info("BotController :: removing [$cPid]")
                try {
                    stopTask("task${pendingClients.remove(k)?.processId}")
                } catch (e: Exception) {
                    logger.info(e.toString())
                }
            }
        }
    }

    private fun addTask(target: () -> Unit, taskName: String) {
        val task = Thread(target, taskName)
        task.isDaemon = true
        tasks[taskName] = task
        task.start()
    }

    private fun stopTask(taskName: String, timeout: Int = 30) {
        tasks[taskName]?.join(timeout * 1000L)
    }

    private fun stopAllTasks(timeout: Int = 30) {
        for ((taskName, task) in tasks) {
            logger.info("stopping task $taskName")
            task.join(timeout * 1000L)
        }
    }

    override fun startBot(client: BotClientWindow) {
        reloadBotConfig(client)
        client.startBot()
        addTask({ runBot(client) }, client.name ?: "unknown")
    }

    private fun runBot(client: BotClientWindow) {
        client.botStatus = BotStatus.STARTED
        logger.info("${client.name}: Started.")

        val functions = getFunctionsForClient(client)
        for (function in functions) {
            if (function.logger.handlers.none { it === ipcLogHandler }) {
                function.logger.addHandler(ipcLogHandler)
            }
        }

        while (client.running) {
            client.botStatus = BotStatus.RUNNING
            if (client.disconnected) {
                logger.info("${client.name}: disconnected.")
                client.closeWindow()
                break
            }
            try {
                for (function in functions) {
                    function.run()
                }
            } catch (e: Exception) {
                logger.log(Level.SEVERE, "bot loop error for ${client.name}", e)
            }
        }
        client.botStatus = BotStatus.STOPPED
        logger.info("${client.name}: Stopped.")
    }

    override fun stopAllBots(timeout: Int) {
        logger.info("stopping all bots...")
        val stopping = mutableListOf<BotClientWindow>()
        for (client in clients.values.toList()) {
            if (client.running) {
                logger.info("stopping client  ${client.name}")
                client.stopBot()
                stopping.add(client)
            }
        }
        for (client in stopping) {
            logger.log(Level.FINE, "joining thread ${client.name}")
            stopTask(client.name ?: "unknown", timeout)
            client.botStatus = BotStatus.STOPPED
        }
    }

    override fun stopBot(client: BotClientWindow, timeout: Int) {
        if (client.running) {
            client.stopBot()
            stopTask(client.name ?: "unknown", timeout)
            client.botStatus = BotStatus.STOPPED
        }
    }

    override fun listen() {
        _running = true
        try {
            controllerStartTime = System.currentTimeMillis()
            addTask({ scanForClients() }, "scan_for_clients")
            server.run()
            while (_running) {
                sleepSeconds(1.0)
            }
        } catch (e: InterruptedException) {
            logger.info("Exiting...")
        } catch (e: Exception) {
            logger.log(Level.SEVERE, "listen error", e)
        }
        shutdown()
    }

    override fun shutdown() {
        super.shutdown()
        stopAllTasks()
    }
}
