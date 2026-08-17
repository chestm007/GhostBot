package com.ghostbot.ipc

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Timeout
import java.net.ServerSocket
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicBoolean

/**
 * End-to-end loopback test: a real TCP socket pair on localhost, exercising
 * the NIO server and the blocking client together (accept, read framing,
 * nested-object messages, multi-message writes, heartbeat).
 */
@Timeout(60)
class IpcLoopbackTest {

    private fun freePort(): Int = ServerSocket(0).use { it.localPort }

    class TestServer(port: Int, val received: MutableList<Message> = CopyOnWriteArrayList<Message>().toMutableList()) :
        IpcServer("localhost", port, heartbeatInterval = 1) {

        override fun dispatch(conn: java.nio.channels.SocketChannel, data: String) {
            for (m in Message.fromJsonHandlingMultiple(data)) {
                m?.let { received.add(it) }
            }
        }
    }

    class TestClient(port: Int, val received: MutableList<Message> = CopyOnWriteArrayList<Message>().toMutableList()) :
        IpcClient("localhost", port) {

        val heartbeats = AtomicBoolean(false)

        override fun dispatchRaw(data: ByteArray) {
            val text = data.toString(Charsets.UTF_8)
            if (Command.fromValue(text.trim()) == Command.SERVER_HEARTBEAT) {
                heartbeats.set(true)
                return
            }
            for (m in Message.fromJsonHandlingMultiple(text)) {
                m?.let { received.add(it) }
            }
        }
    }

    private fun await(condition: () -> Boolean, timeoutMs: Long = 10000, what: String): Boolean {
        val deadline = System.currentTimeMillis() + timeoutMs
        while (System.currentTimeMillis() < deadline) {
            if (condition()) return true
            Thread.sleep(50)
        }
        assertTrue(condition(), "timed out waiting for: $what")
        return false
    }

    @Test
    fun `client and server exchange messages over a real socket`() {
        val port = freePort()
        val serverReceived = mutableListOf<Message>()
        val clientReceived = mutableListOf<Message>()
        val server = TestServer(port, serverReceived)
        val client = TestClient(port, clientReceived)

        server.setupServer()
        server.startListeningThread()
        client.run()

        try {
            // 1. client -> server
            client.sendMessage(Message(Command.START, "loopback_char"))
            await(
                { serverReceived.any { it.command == Command.START } },
                what = "server to receive START"
            )
            assertEquals("loopback_char", serverReceived.first { it.command == Command.START }.target)

            // 2. server -> client
            server.sendToAll(Message(Command.INFO, "char1 char2"))
            await(
                { clientReceived.any { it.command == Command.INFO } },
                what = "client to receive INFO"
            )
            assertEquals("char1 char2", clientReceived.first { it.command == Command.INFO }.target)

            // 3. nested object target (exercises the server-side JSON framing)
            val nested = Message(
                Command.CONFIG_GET,
                mapOf(
                    "action" to "get",
                    "char" to "Lilith",
                    "config" to mapOf("attack" to mapOf("spot" to (1 to 2))),
                )
            )
            client.sendMessage(nested)
            await(
                { serverReceived.any { it.command == Command.CONFIG_GET } },
                what = "server to receive CONFIG_GET"
            )
            val got = serverReceived.first { it.command == Command.CONFIG_GET }
            val dict = got.targetAsDict()!!
            assertEquals("Lilith", dict["char"])
            @Suppress("UNCHECKED_CAST")
            val config = dict["config"] as Map<String, Any?>
            // JSON has no tuples — a pair round-trips as a 2-element list (same in Python).
            assertEquals(mapOf("spot" to listOf(1, 2)), config["attack"])

            // 4. two messages written back-to-back in a single write
            val two = Message(Command.START, "a").toString() + Message(Command.STOP, "b").toString()
            client.sendMessage(two)
            await(
                { serverReceived.count { it.command == Command.START } >= 2 },
                what = "second START"
            )
            await(
                { serverReceived.any { it.command == Command.STOP && it.target == "b" } },
                what = "STOP b"
            )

            // 5. heartbeat (server interval is 1s in this test)
            await({ client.heartbeats.get() }, timeoutMs = 5000, what = "heartbeat")
        } finally {
            client.stop()
            server.closeAllConnections()
        }
    }
}
