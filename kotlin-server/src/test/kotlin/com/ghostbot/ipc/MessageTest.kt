package com.ghostbot.ipc

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

/**
 * Port of the runnable parts of the IPC message tests: wire-format round trips
 * and the multi-document splitter (the `}{` concatenation the Python relies on).
 */
class MessageTest {

    @Test
    fun `command values match the wire protocol`() {
        assertEquals(-2, Command.ERROR.value)
        assertEquals(-1, Command.EXIT.value)
        assertEquals(1, Command.INFO.value)
        assertEquals(2, Command.INFO_CHAR.value)
        assertEquals(3, Command.INFO_AUTOLOGIN.value)
        assertEquals(10, Command.START.value)
        assertEquals(20, Command.STOP.value)
        assertEquals(30, Command.CONFIG.value)
        assertEquals(31, Command.CONFIG_GET.value)
        assertEquals(32, Command.CONFIG_SET.value)
        assertEquals(33, Command.CONFIG_AUTOLOGIN_GET.value)
        assertEquals(34, Command.CONFIG_AUTOLOGIN_SET.value)
        assertEquals(35, Command.CONFIG_AUTOLOGIN_DELETE.value)
        assertEquals(40, Command.OPEN_CLIENT.value)
        assertEquals(41, Command.CLOSE_CLIENT.value)
        assertEquals(100, Command.LOG.value)
        assertEquals(200, Command.SERVER_HEARTBEAT.value)
    }

    @Test
    fun `from str is case-insensitive`() {
        assertEquals(Command.START, Command.fromStr("START"))
        assertEquals(Command.START, Command.fromStr("start"))
        assertEquals(Command.CONFIG_SET, Command.fromStr("config_set"))
        assertNull(Command.fromStr("notacommand"))
    }

    @Test
    fun `from value parses the heartbeat wire int`() {
        assertEquals(Command.SERVER_HEARTBEAT, Command.fromValue("200"))
        assertEquals(Command.EXIT, Command.fromValue("-1"))
        assertNull(Command.fromValue("nope"))
        assertNull(Command.fromValue("99999"))
    }

    @Test
    fun `message round trips through the wire format`() {
        val m = Message(Command.START, "iSuckYouDry")
        assertEquals("""{"command":"start","target":"iSuckYouDry"}""", m.toString())
        val back = Message.fromJson(m.toString())!!
        assertEquals(Command.START, back.command)
        assertEquals("iSuckYouDry", back.target)
    }

    @Test
    fun `message with dict target round trips`() {
        val m = Message(Command.CONFIG_GET, mapOf("action" to "get", "char" to "Lilith"))
        val back = Message.fromJson(m.toString())!!
        assertEquals(Command.CONFIG_GET, back.command)
        assertEquals(mapOf("action" to "get", "char" to "Lilith"), back.target)
    }

    @Test
    fun `message with null target`() {
        val m = Message(Command.EXIT)
        assertTrue(m.toString().contains("\"target\":null"))
        val back = Message.fromJson(m.toString())!!
        assertNull(back.target)
    }

    @Test
    fun `multiple concatenated messages split correctly`() {
        val a = Message(Command.START, "a")
        val b = Message(Command.STOP, "b")
        val combined = a.toString() + b.toString()
        val messages = Message.fromJsonHandlingMultiple(combined)
        assertEquals(2, messages.size)
        assertEquals(Command.START, messages[0].command)
        assertEquals("a", messages[0].target)
        assertEquals(Command.STOP, messages[1].command)
        assertEquals("b", messages[1].target)
    }

    @Test
    fun `invalid json returns null`() {
        assertNull(Message.fromJson("not json at all"))
        assertNull(Message.fromJson("""{"command": "notacommand"}"""))
    }

    @Test
    fun `heartbeat is detected via from value`() {
        // the Python checks `Command.from_value(data) == SERVER_HEARTBEAT`
        assertEquals(Command.SERVER_HEARTBEAT, Command.fromValue("200"))
        assertFalse(Command.fromValue("1") == Command.SERVER_HEARTBEAT)
    }
}
