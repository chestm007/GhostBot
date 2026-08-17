package com.ghostbot

import com.ghostbot.lib.sleepSeconds
import com.ghostbot.win32.ProcessMemory
import java.io.File

/**
 * Port of GhostBot/client_launcher.py.
 *
 * Launches the Talisman Online game client (`game.exe`) and clicks through the
 * launcher (Genesis -> Enter Game) to reach the login screen.
 */
class ClientLauncher : Win32ClientWindow(initProcess()) {

    companion object {
        const val PATH = "C:\\Program Files (x86)\\TalismanOnline"
        const val EXE = "game.exe"

        /**
         * Port of the `__init__` no-process path: if no `game.exe` is running,
         * launch it and wait for the process to appear.
         */
        fun initProcess(): ProcessMemory {
            val existing = ProcessMemory.getProcMatching(EXE)
            return if (existing.isNotEmpty()) {
                existing.first()
            } else {
                val game = File(PATH, EXE)
                if (!game.exists()) {
                    throw java.io.FileNotFoundException("game.exe not found at $PATH")
                }
                // Port of `win32api.WinExec` (non-blocking start).
                ProcessBuilder(game.absolutePath)
                    .directory(File(PATH))
                    .inheritIO()
                    .start()
                // wait briefly for the process to appear
                var attempts = 0
                while (attempts < 50) {
                    val procs = ProcessMemory.getProcMatching(EXE)
                    if (procs.isNotEmpty()) return procs.first()
                    sleepSeconds(0.2)
                    attempts++
                }
                throw IllegalStateException("game launcher process didnt launch")
            }
        }
    }

    /** Port of `block_until_ready`. */
    fun blockUntilReady(): ClientLauncher {
        sleepSeconds(1.0)
        leftClick(480 to 335) // Genesis
        sleepSeconds(1.5)
        leftClick(480 to 455) // Enter Game
        sleepSeconds(6.0)
        return this
    }
}
