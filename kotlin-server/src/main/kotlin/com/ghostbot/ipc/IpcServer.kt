package com.ghostbot.ipc

import com.ghostbot.rootLogger
import java.io.IOException
import java.net.InetSocketAddress
import java.net.StandardSocketOptions
import java.nio.ByteBuffer
import java.nio.channels.SelectionKey
import java.nio.channels.Selector
import java.nio.channels.ServerSocketChannel
import java.nio.channels.SocketChannel
import java.util.concurrent.ConcurrentHashMap
import java.util.logging.Handler
import java.util.logging.Level
import java.util.logging.LogRecord

/**
 * Port of GhostBot/IPC/server.py `IPCServer`.
 *
 * NIO selector based: one listening thread, non-blocking accept/read,
 * heartbeats to all clients after `heartbeatInterval` seconds of idle time.
 *
 * The Python server dispatches raw 1024-byte chunks (a JSON document may be
 * split across chunks, or several may arrive in one chunk); each side recovers
 * by splitting on `}{`. This port accumulates per-connection bytes and splits
 * on the `}` boundary instead, so `dispatch` always receives complete JSON
 * documents — compatible with the existing Python client and free of the
 * chunk-boundary race.
 */
abstract class IpcServer(
    val host: String = "localhost",
    val port: Int = 64057,
    val heartbeatInterval: Long = 5,
) {
    val logger = java.util.logging.Logger.getLogger("GhostBot.IpcServer")

    private var serverSocket: ServerSocketChannel? = null
    private var selector: Selector? = null
    var listeningThread: Thread? = null
        private set
    private var lastHeartbeatTime = System.currentTimeMillis()
    @Volatile
    var running: Boolean = false
        private set

    /** {connection -> read/last-activity state}. */
    private val clients = ConcurrentHashMap<SocketChannel, ClientState>()
    /** {connection -> its SelectionKey} (this JDK's Selector lacks keyFor()). */
    private val keys = ConcurrentHashMap<SocketChannel, SelectionKey>()

    private class ClientState {
        var lastActivity = System.currentTimeMillis()
        val pending = StringBuilder()
    }

    /**
     * Override with your implementation.
     * Called with one or more complete JSON documents concatenated.
     */
    protected abstract fun dispatch(conn: SocketChannel, data: String)

    /** Hook called after a new connection is registered. */
    protected open fun onAccept(conn: SocketChannel) {}

    fun setupServer() {
        val socket = ServerSocketChannel.open().apply {
            configureBlocking(false)
            setOption(StandardSocketOptions.SO_REUSEADDR, true)
        }
        socket.bind(InetSocketAddress(host, port))
        serverSocket = socket
        val sel = Selector.open()
        socket.register(sel, SelectionKey.OP_ACCEPT)
        selector = sel
        logger.info("Server listening on $host:$port...")
        running = true
    }

    fun accept(sock: ServerSocketChannel) {
        val conn = sock.accept() ?: return
        logger.info("Accepted connection from ${addr(conn)}")
        conn.configureBlocking(false)
        val key = conn.register(selector!!, SelectionKey.OP_READ)
        keys[conn] = key
        clients[conn] = ClientState()
        onAccept(conn)
    }

    private fun read(conn: SocketChannel) {
        val state = clients[conn] ?: return
        val buf = ByteBuffer.allocate(1024)
        val n = try {
            conn.read(buf)
        } catch (e: IOException) {
             logger.severe("Client ${addr(conn)} reset the connection.")
             removeClient(conn)
             return
         }
        if (n <= 0) {
            logger.info("Client ${addr(conn)} disconnected.")
            removeClient(conn)
            return
        }
        buf.flip()
        state.lastActivity = System.currentTimeMillis()
        state.pending.append(String(buf.array(), buf.position(), buf.remaining(), Charsets.UTF_8))
        drain(state, conn)
    }

    /**
     * Split the accumulated buffer into complete top-level JSON documents and
     * dispatch them. Uses brace-depth tracking (string-aware), so nested
     * objects inside `target` don't cause premature cuts and partial
     * documents are never dispatched.
     */
    private fun drain(state: ClientState, conn: SocketChannel) {
        while (true) {
            val end = findCompleteDocEnd(state.pending)
            if (end == -1) break
            val complete = state.pending.substring(0, end)
            state.pending.delete(0, end)
            try {
                dispatch(conn, complete)
            } catch (e: Exception) {
                logger.log(Level.SEVERE, "dispatch error", e)
            }
        }
    }

    /**
     * Index just past the end of the first complete top-level JSON object in
     * [s], or -1 if none. String-aware (skips `{`/`}` inside JSON strings).
     */
    private fun findCompleteDocEnd(s: StringBuilder): Int {
        var depth = 0
        var inString = false
        var escaped = false
        var started = false
        for (i in 0 until s.length) {
            val c = s[i]
            if (inString) {
                when {
                    escaped -> escaped = false
                    c == '\\' -> escaped = true
                    c == '"' -> inString = false
                }
            } else when (c) {
                '"' -> inString = true
                '{' -> {
                    depth++
                    started = true
                }
                '}' -> {
                    depth--
                    if (started && depth == 0) return i + 1
                }
            }
        }
        return -1
    }

    fun sendToAll(message: Message) {
        for (conn in clients.keys.toList()) sendToClient(conn, message)
    }

    /** Raw-string broadcast (heartbeats). */
    fun sendToAllRaw(message: String) {
        val bytes = message.toByteArray(Charsets.UTF_8)
        for (conn in clients.keys.toList()) {
            try {
                conn.write(ByteBuffer.wrap(bytes))
            } catch (e: Exception) {
                logger.log(Level.SEVERE, "send error", e)
                removeClient(conn)
            }
        }
    }

    fun sendToClient(conn: SocketChannel, message: Message) {
        sendRaw(conn, message.toString())
    }

    fun sendRaw(conn: SocketChannel, message: String) {
        try {
            conn.write(ByteBuffer.wrap(message.toByteArray(Charsets.UTF_8)))
        } catch (e: Exception) {
            logger.log(Level.SEVERE, "Error sending to ${addr(conn)}", e)
            removeClient(conn)
        }
    }

    fun removeClient(conn: SocketChannel) {
        if (clients.remove(conn) != null) {
            runCatching { keys.remove(conn)?.cancel() }
            runCatching { conn.close() }
        }
    }

    private fun sendHeartbeats() {
        val now = System.currentTimeMillis()
        if (now - lastHeartbeatTime >= heartbeatInterval * 1000) {
            logger.fine("Sending heartbeats...")
            sendToAllRaw(Command.SERVER_HEARTBEAT.value.toString())
            lastHeartbeatTime = now
        }
    }

    fun startListeningThread() {
        val t = Thread({
            try {
                val sel = selector ?: return@Thread
                while (running) {
                    sel.select(1000)
                    val keys = sel.selectedKeys()
                    if (keys.isEmpty()) {
                        sendHeartbeats()
                        continue
                    }
                    val iter = keys.iterator()
                    while (iter.hasNext()) {
                        val key = iter.next()
                        iter.remove()
                        if (!key.isValid) continue
                        when {
                            key.isAcceptable -> accept(key.channel() as ServerSocketChannel)
                            key.isReadable -> read(key.channel() as SocketChannel)
                        }
                    }
                    Thread.sleep(50)
                }
            } catch (e: InterruptedException) {
                // shutting down
            } catch (e: Exception) {
                logger.log(Level.SEVERE, "listening thread error", e)
            } finally {
                closeAllConnections()
            }
        }, "ipc-server")
        t.isDaemon = true
        t.start()
        listeningThread = t
    }

    fun run() {
        setupServer()
        Thread.sleep(1000)
        startListeningThread()
    }

    fun closeAllConnections() {
        running = false
        for ((conn, key) in keys) runCatching { key.cancel() }
        keys.clear()
        serverSocket?.let { runCatching { it.close() } }
        for (conn in clients.keys.toList()) removeClient(conn)
        runCatching { selector?.close() }
        logger.info("All connections closed.")
    }

    private fun addr(conn: SocketChannel): String =
        runCatching { (conn.getRemoteAddress() as? InetSocketAddress)?.address?.hostAddress ?: "?" }
            .getOrDefault("?")
}

/**
 * Port of GhostBot/IPC/server.py `IPCServerLogHandler`.
 * Forwards log records (at or above the IPC server's logger level) to all
 * connected clients as `Command.LOG` messages.
 */
class IpcServerLogHandler(private val ipcServer: IpcServer) : Handler() {
    override fun publish(record: LogRecord) {
        // Python: `record.levelno >= self._ipc_server.logger.level`. An unset
        // logger level is NOTSET (0) there, so the comparison always passes. In
        // this JUL an unset level is null — fall back to 0 to mirror that, and
        // never let a forwarding failure break the dispatch path.
        val threshold = ipcServer.logger.level?.intValue() ?: 0
        if (record.level.intValue() >= threshold) {
            runCatching {
                ipcServer.sendToAll(Message(Command.LOG, formatter.format(record)))
            }
        }
    }

    override fun close() {}
    override fun flush() {}
}
