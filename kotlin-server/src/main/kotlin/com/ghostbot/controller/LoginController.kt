package com.ghostbot.controller

import com.ghostbot.ImageFinder
import com.ghostbot.config.LoginDetailsConfigLoader
import com.ghostbot.lib.UILocations
import com.ghostbot.lib.retry
import com.ghostbot.lib.retryWithCount
import com.ghostbot.lib.sleepSeconds
import com.ghostbot.rootLogger
import java.io.File
import java.util.logging.Level
import java.util.concurrent.locks.ReentrantLock

/**
 * Port of GhostBot/controller/login_controller.py.
 */

/**
 * Class-level lock so only one login procedure runs at a time.
 * Mirrors `LoginLock` (the Python `threading.Lock` classproperty behaviour).
 */
object LoginLock {
    private val lock = ReentrantLock(true)
    @Volatile
    private var lockedProcId: String = ""

    val logger = java.util.logging.Logger.getLogger("GhostBot.LoginLock")

    fun acquire(procId: String, timeout: Double = 30.0): LoginLock {
      val startTime = System.currentTimeMillis()
      while (true) {
          if (lock.tryLock(1L, java.util.concurrent.TimeUnit.SECONDS)) {
              lockedProcId = procId
              return this
          }
          if (timeout > 0 && (System.currentTimeMillis() - startTime) / 1000.0 > timeout) {
              throw java.util.concurrent.TimeoutException(
                  "LoginLock :: timed out waiting for lock to be unlocked after ${timeout}s"
              )
          }
          logger.log(Level.FINE, "LoginLock :: waiting for lock to be unlocked, polling...")
      }
    }

    fun release(): LoginLock {
        if (lock.isHeldByCurrentThread) {
            lock.unlock()
        }
        lockedProcId = ""
        return this
    }

    val locked: Boolean get() = lock.isLocked
    val unlocked: Boolean get() = !lock.isLocked

    /** Port of the `with LoginLock()` context manager. */
    inline fun <T> withLock(block: () -> T): T {
        acquire("context")
        try {
            return block()
        } finally {
            release()
        }
    }
}

class LoginController(
    private val client: BotClientWindow,
    private val botController: BotController,
) {
    companion object {
        val loginLock = LoginLock
    }

    enum class LoginStage {
        ENTER_CREDENTIALS,
        SERVER_SELECT,
        LOGIN_QUEUE,
        CHARACTER_SELECT,
        SUCCESS,
    }

    private val logger = java.util.logging.Logger.getLogger("GhostBot.LoginController")
    private var config: LoginDetailsConfigLoader.CharDetails? = null
    private val imageFinder = ImageFinder(client)
    private var serverBusyRetries = 0

    fun setConfig(config: LoginDetailsConfigLoader.CharDetails) {
        this.config = config
    }

    private val enterCredentials: Boolean
        get() = imageFinder.findUiElement(
            File(ImageFinder.miscFolder, "login_main_page.bmp").path, threshold = 0.6
        ) != null

    private val serverSelect: Boolean
        get() = imageFinder.findUiElement(
            File(ImageFinder.miscFolder, "login_server_select.bmp").path
        ) != null

    private val loginQueue: Boolean
        get() = imageFinder.findUiElement(
            File(ImageFinder.miscFolder, "login_queue.bmp").path
        ) != null

    private val characterSelect: Boolean
        get() {
            val level = client.level
            if (level != null) return false
            return !(enterCredentials || serverSelect || loginQueue)
        }

    val currentStage: LoginStage
        get() = when {
            enterCredentials -> LoginStage.ENTER_CREDENTIALS
            serverSelect -> LoginStage.SERVER_SELECT
            loginQueue -> LoginStage.LOGIN_QUEUE
            characterSelect -> LoginStage.CHARACTER_SELECT
            else -> LoginStage.SUCCESS
        }

    private fun handleStage() {
        when (currentStage) {
            LoginStage.ENTER_CREDENTIALS -> handleEnterCredentials()
            LoginStage.SERVER_SELECT -> handleServerSelect()
            LoginStage.LOGIN_QUEUE -> handleLoginQueue()
            LoginStage.CHARACTER_SELECT -> handleCharacterSelect()
            LoginStage.SUCCESS -> throw TypeError("unexpected stage SUCCESS")
        }
    }

    private class TypeError(msg: String) : RuntimeException(msg)

    private fun handleEnterCredentials() {
        logger.log(Level.FINE, "${client.identifier} :: enter credentials")
        val conf = config ?: return
        client.nameCache = conf.charName
        repeat(20) {
            client.pressKey("backspace")
        }
        sleepSeconds(1.0)
        client.typeKeys(conf.username, charOnly = true)
        client.pressKey("tab")
        client.typeKeys(conf.password, charOnly = true)
        client.pressKey("enter")

        if (!retry({ serverSelect }, retries = 3, delay = 2.0)) {
            serverBusyRetries++
            logger.log(
                Level.FINE,
                "${client.identifier} :: login server is busy, restarting login process... (retry $serverBusyRetries/3)"
            )
            client.leftClick(510 to 335) // 'login server is busy' dialog
            sleepSeconds(0.5)
            client.leftClick(620 to 390) // username text box

            if (serverBusyRetries >= 3) {
                logger.severe("${client.identifier} :: max 'server busy' retries reached, aborting login")
                throw RuntimeException("Max server busy retries reached")
            }
        } else {
            // Moved to server_select stage or succeeded, reset counter
            serverBusyRetries = 0
        }
    }

    private fun handleServerSelect() {
        loginLock.release()
        logger.log(Level.FINE, "${client.identifier} :: server select")
        val server = config?.server
        if (server != null && server.isNotEmpty()) {
            client.leftClick(UILocations.ServerSelect.byName[server] ?: UILocations.ServerSelect.ok)
            sleepSeconds(1.0)
        }
        client.leftClick(UILocations.ServerSelect.ok)
    }

    private fun handleLoginQueue() {
        logger.log(Level.FINE, "${client.identifier} :: login queue, waiting 30s")
        sleepSeconds(25.0)
    }

    private fun handleCharacterSelect() {
        logger.log(Level.FINE, "${client.identifier} :: character select")
        fun selectChar(retryCount: Int): Boolean {
            logger.log(Level.FINE, "${client.identifier} :: waiting for game entered... (attempt $retryCount)")
            client.leftClick(UILocations.charSelectEnterGame)
            sleepSeconds(1.0)
            client.initializePointers(forceReload = true)
            return currentStage == LoginStage.SUCCESS
        }

        if (retryWithCount(::selectChar, retries = 5, delay = 1.0)) {
            logger.info("${client.identifier} :: character logged in")
            client.postLoginSetup()
        } else {
            logger.info("${client.identifier} :: character interrupted")
            client.leftClick(UILocations.charSelectInterruptedOk)
        }
    }

    /**
     * Drives the login stages until the client's level becomes readable
     * (i.e. the character is in game), or the controller stops running.
     * Calls [callback] with true on success, false on failure.
     */
    fun handleLogin(callback: (Boolean) -> Unit) {
        logger.log(Level.FINE, "${client.identifier} :: handle login")
        var success = false
        while (client.level == null) {
            if (!botController.running) {
                logger.log(Level.FINE, "${client.identifier} :: bot controller not running, exiting...")
                return
            }
            try {
                client.setWindowName()
                handleStage()
                // Initialize the memory pointers, as they can't be set before login.
                client.setWindowName()
            } catch (e: Exception) {
                // pywintypes.error 'Invalid window handle.' / TypeError in the Python
                logger.log(Level.SEVERE, "login stage error for ${client.identifier}", e)
                break
            }
            sleepSeconds(1.0)
        }
        if (client.level != null) {
            logger.info("${client.identifier} :: login handled")
            success = true
        } else {
            logger.severe("${client.identifier} :: login failed")
        }
        callback(success)
    }
}
