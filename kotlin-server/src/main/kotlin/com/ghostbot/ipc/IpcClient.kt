package com.ghostbot.ipc

import com.ghostbot.rootLogger
import com.ghostbot.lib.retry
import java.net.InetSocketAddress
import java.net.Socket
import java.net.SocketException
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.logging.Level

/**
 * Port of GhostBot/IPC/client.py `IPCClient`.
 *
 * One blocking socket read on a daemon reader thread; sends are synchronized
 * on the socket (the Python client did the same, from multiple threads).
 * Subclasses override [dispatchRaw] (Python `_dispatch(data: bytes)`).
 */
abstract class IpcClient(
    val host: String = "localhost",
    val port: Int = 64057,
) {
    val logger = java.util.logging.Logger.getLogger("GhostBot.IpcClient")

    @Volatile
    var running: Boolean = false
        protected set

    private var clientSocket: Socket? = null
    private var listener: Thread? = null
    private val sendLock = Any()

    /** Port of `IPCClient._dispatch(data: bytes)`. */
    protected abstract fun dispatchRaw(data: ByteArray)

    private fun connect() {
        val sock = Socket()
        sock.soTimeout = 0
        try {
            sock.connect(InetSocketAddress(host, port), 5000)
            clientSocket = sock
            logger.info("Connected to server at $host:$port")
            Thread.sleep(500)
            running = true
        } catch (e: java.net.ConnectException) {
            logger.severe("Connection refused by server at $host:$port.")
            runCatching { sock.close() }
            running = false
        } catch (e: Exception) {
            logger.severe("Error connecting to server.")
            logger.log(Level.SEVERE, "connect error", e)
            runCatching { sock.close() }
            running = false
        }
    }

    private fun readerLoop() {
        val sock = clientSocket
        if (sock == null) return
        val buf = ByteArray(1024)
        try {
            while (running) {
                val n = try {
                    sock.getInputStream().read(buf)
                } catch (e: SocketException) {
                    0
                }
                if (n == -1) {
                    logger.info("Server closed the connection.")
                    stop()
                    return
                }
                if (n > 0) {
                    logger.fine("Received from server: ${String(buf, 0, n)}")
                    try {
                        dispatchRaw(buf.copyOf(n))
                    } catch (e: Exception) {
                        logger.log(Level.SEVERE, "dispatch error", e)
                    }
                }
            }
        } catch (e: Exception) {
            logger.severe("Server reset the connection.")
            logger.log(Level.SEVERE, "read error", e)
            stop()
        }
    }

    private fun reconnect(): Boolean {
        if (!running) {
            logger.fine("Client is not running, reconnecting...")
            connect()
            if (running) startListeningThread()
        }
        return running
    }

    fun sendMessage(message: String) {
        if (!retry({ reconnect() }, retries = 5, delay = 2.0)) {
            logger.severe("Could not reconnect to server.")
            return
        }
        val sock = clientSocket ?: run {
            logger.severe("Error sending message, no client socket available.")
            return
        }
        try {
            synchronized(sendLock) {
                sock.getOutputStream().write(message.toByteArray(Charsets.UTF_8))
                sock.getOutputStream().flush()
            }
        } catch (e: java.net.SocketException) {
            logger.severe("Could not send message. Server connection lost.")
            stop()
        } catch (e: Exception) {
            logger.severe("Error sending message. $message")
            logger.log(Level.SEVERE, "send error", e)
            stop()
        }
    }

    fun sendMessage(message: Message) = sendMessage(message.toString())

    private fun startListeningThread() {
        if (listener?.isAlive == true) return
        val t = Thread({ readerLoop() }, "ipc-client")
        t.isDaemon = true
        t.start()
        listener = t
    }

    fun run() {
        connect()
        if (!running) return
        Thread.sleep(500)
        startListeningThread()
    }

    fun stop() {
        logger.info("Client shutting down.")
        running = false
        val sock = clientSocket
        if (sock != null) {
            runCatching { sock.close() }
        }
        clientSocket = null
        logger.info("Client connection closed.")
    }

    fun join(timeoutMs: Long) {
        runCatching { listener?.join(timeoutMs) }
    }
}
