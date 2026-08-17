package com.ghostbot.win32

import com.sun.jna.Memory
import com.sun.jna.Native
import com.sun.jna.Pointer
import com.sun.jna.Library
import com.sun.jna.platform.win32.GDI32
import com.sun.jna.platform.win32.Kernel32
import com.sun.jna.platform.win32.Tlhelp32
import com.sun.jna.platform.win32.User32
import com.sun.jna.platform.win32.WinDef
import com.sun.jna.platform.win32.WinGDI
import com.sun.jna.platform.win32.WinNT
import com.sun.jna.platform.win32.WinUser.WNDENUMPROC
import com.sun.jna.ptr.IntByReference
import com.ghostbot.rootLogger
import java.util.concurrent.ConcurrentHashMap

/**
 * Port of the pywin32/pymem Win32 layer (GhostBot/client_window.py +
 * GhostBot/lib/win32/process.py).
 *
 * NOTE: targets the JNA fork served by this environment's Maven repo
 * (FFI-based `Structure`, no `Pointer.use/isNull`). Uses the provided
 * jna-platform `User32`/`GDI32`/`Kernel32` interfaces plus a small
 * [User32Ext] for the W-function variants the fork's User32 omits.
 *
 * Win32 message constants ported from GhostBot/lib/vk_codes.py.
 */
object Win32Messages {
    const val WM_DESTROY: Int = 0x0002
    const val WM_MOUSEMOVE: Int = 0x0200
    const val WM_LBUTTONDOWN: Int = 0x0201
    const val WM_LBUTTONUP: Int = 0x0202
    const val WM_RBUTTONDOWN: Int = 0x0204
    const val WM_RBUTTONUP: Int = 0x0205
    const val WM_KEYDOWN: Int = 0x0100
    const val WM_KEYUP: Int = 0x0101
    const val WM_CHAR: Int = 0x0102
}

typealias HWND = WinDef.HWND
typealias HANDLE = WinNT.HANDLE
typealias WPARAM = WinDef.WPARAM
typealias LPARAM = WinDef.LPARAM
typealias RECT = WinDef.RECT
typealias POINT = WinDef.POINT
typealias LRESULT = WinDef.LRESULT
typealias HDC = WinDef.HDC
typealias HBITMAP = WinDef.HBITMAP

/** W-function variants missing from this JNA fork's User32. */
private interface User32Ext : Library {
    fun GetWindowDC(hwnd: HWND): HDC
    fun SetWindowTextW(hwnd: HWND, text: String): Boolean
    fun GetWindowTextW(hwnd: HWND, buffer: Pointer, maxCount: Int): Int
    fun SendMessageW(hwnd: HWND, msg: Int, wParam: WPARAM, lParam: LPARAM): LRESULT
}

object AccessRights {
    const val PROCESS_QUERY_INFORMATION: Int = 0x0400
    const val PROCESS_VM_READ: Int = 0x0010
    const val PROCESS_VM_WRITE: Int = 0x0020
}

/**
 * Windows window handle management, ported from GhostBot/client_window.py
 * `get_hwnds_for_pid` and the Win32ClientWindow window-related methods.
 */
object Win32 {
    private val user32: User32 by lazy { Native.load("user32", User32::class.java) }
    private val user32Ext: User32Ext by lazy { Native.load("user32", User32Ext::class.java) }
    private val gdi32: GDI32 by lazy { Native.load("gdi32", GDI32::class.java) }
    val kernel32: Kernel32 by lazy { Native.load("kernel32", Kernel32::class.java) }

    /** SRCCOPY raster op. */
    const val SRCCOPY: Int = 0x00CC0020

    /** SM_CYCAPTION */
    const val SM_CYCAPTION: Int = 4

    private val logger = java.util.logging.Logger.getLogger("GhostBot.Win32")

    /** Port of `get_hwnds_for_pid`. */
    fun getHwndsForPid(pid: Int): List<HWND> {
        val hwnds = mutableListOf<HWND>()
        val proc = WNDENUMPROC { hwnd, _ ->
            try {
                if (user32.IsWindowVisible(hwnd) && user32.IsWindowEnabled(hwnd)) {
                    val pidRef = IntByReference()
                    user32.GetWindowThreadProcessId(hwnd, pidRef)
                    if (pidRef.value == pid) hwnds.add(hwnd)
                }
            } catch (e: Exception) {
                logger.warning("EnumWindows callback error: $e")
            }
            true
        }
        user32.EnumWindows(proc, null)
        return hwnds
    }

    fun getWindowText(hwnd: HWND): String {
        val len = user32.GetWindowTextLength(hwnd)
        if (len <= 0) return ""
        return Memory((len + 1).toLong()).use { buf ->
            user32Ext.GetWindowTextW(hwnd, buf, len + 1)
            buf.getString(0, "UTF-16LE")
        }
    }

    fun setWindowText(hwnd: HWND, text: String) {
        user32Ext.SetWindowTextW(hwnd, text)
    }

    fun sendMessage(hwnd: HWND, msg: Int, wParam: Long = 0, lParam: Long = 0) {
        user32Ext.SendMessageW(hwnd, msg, WPARAM(wParam), LPARAM(lParam))
    }

    /** Port of the `MAKELONG` used by left/right click. */
    fun makeLong(x: Int, y: Int): Long = (y and 0xFFFF).toLong() shl 16 or (x and 0xFFFF).toLong()

    /**
     * Capture the window of [hwnd] as a top-down RGBA byte array.
     * Port of `Win32ClientWindow.capture_window`.
     */
    fun captureWindow(hwnd: HWND, width: Int, height: Int): ByteArray? {
        val hdc = user32Ext.GetWindowDC(hwnd)
        val compatDc = gdi32.CreateCompatibleDC(hdc)
        val bitmap = gdi32.CreateCompatibleBitmap(hdc, width, height)
        val oldObj = gdi32.SelectObject(compatDc, bitmap)
        try {
            gdi32.BitBlt(compatDc, 0, 0, width, height, hdc, 0, 0, SRCCOPY)

            val bmi = WinGDI.BITMAPINFO()
            val header = WinGDI.BITMAPINFOHEADER().apply {
                biSize = 40
                biWidth = width
                biHeight = height
                biPlanes = 1
                biBitCount = 24
                biCompression = 0
            }
            bmi.bmiHeader = header

            val bits = Memory((width.toLong() * height * 4))
            val lines = gdi32.GetDIBits(compatDc, bitmap, 0, height, bits, bmi, 0 /* DIB_RGB_COLORS */)
            if (lines <= 0) return null
            // DIBs are bottom-up; flip to top-down RGBA.
            val out = ByteArray(width * height * 4)
            val rowBytes = width * 4
            for (y in 0 until height) {
                val srcOffset = (height - 1 - y) * rowBytes
                val dstOffset = y * rowBytes
                for (x in 0 until width) {
                    val s = (srcOffset + x * 4).toLong()
                    val d = dstOffset + x * 4
                    // BGRA -> RGBA
                    out[d] = bits.getByte(s + 2)
                    out[d + 1] = bits.getByte(s + 1)
                    out[d + 2] = bits.getByte(s)
                    out[d + 3] = bits.getByte(s + 3)
                }
            }
            return out
        } finally {
            if (!oldObj.equals(Pointer.NULL)) gdi32.SelectObject(compatDc, oldObj)
            gdi32.DeleteObject(bitmap)
            gdi32.DeleteDC(compatDc)
            user32.ReleaseDC(hwnd, hdc)
        }
    }

    fun getWindowRect(hwnd: HWND): RECT? =
        RECT().takeIf { user32.GetWindowRect(hwnd, it) }

    fun getSystemMetrics(index: Int): Int = user32.GetSystemMetrics(index)

    fun getCursorPos(): POINT? =
        POINT().takeIf { user32.GetCursorPos(it) }
}

/**
 * Port of GhostBot/lib/win32/process.py — process enumeration + memory access,
 * replacing `pymem`. Only the APIs the server portion uses are implemented.
 */
class ProcessMemory(val processId: Int) {
    companion object {
        private val logger = java.util.logging.Logger.getLogger("GhostBot.ProcessMemory")
        private val openHandles = ConcurrentHashMap<Int, HANDLE>()

        /** Port of `PymemProcess.get_proc_matching(match)`. */
        fun getProcMatching(match: String): List<ProcessMemory> {
            val result = mutableListOf<ProcessMemory>()
            val k32 = Win32.kernel32
            val snapshot = k32.CreateToolhelp32Snapshot(Tlhelp32.TH32CS_SNAPPROCESS, WinDef.DWORD(0))
            try {
                val pe = Tlhelp32.PROCESSENTRY32().apply {
                    dwSize = WinDef.DWORD(size().toLong())
                }
                if (!k32.Process32First(snapshot, pe)) return result
                do {
                    val exe = pe.szExeFile?.toString()?.lowercase()
                    val pid = pe.th32ProcessID.toInt()
                    if (exe == match.lowercase()) {
                        try {
                            result.add(ProcessMemory(pid))
                        } catch (e: Exception) {
                            logger.info(
                                "could not open process ($pid), maybe it hasnt logged in yet, " +
                                    "or is running as Administrator? skipping..."
                            )
                        }
                    }
                } while (k32.Process32Next(snapshot, pe))
                return result
            } finally {
                runCatching { k32.CloseHandle(snapshot) }
            }
        }

        /** Port of `PymemProcess.list_clients`. */
        fun listClients(): List<ProcessMemory> = getProcMatching("client.exe")

        /** Port of `PymemProcess.get_game_exe`. */
        fun getGameExe(): ProcessMemory {
            val games = getProcMatching("game.exe")
            if (games.size > 1) throw NoSuchElementException("too many game launcher processes detected, there can only be one")
            return games.firstOrNull() ?: throw NoSuchElementException("no game.exe process found")
        }
    }

    private val handle: HANDLE = synchronized(openHandles) {
        openHandles.getOrPut(processId) {
            Win32.kernel32.OpenProcess(
                AccessRights.PROCESS_QUERY_INFORMATION or
                    AccessRights.PROCESS_VM_READ or
                    AccessRights.PROCESS_VM_WRITE,
                false,
                processId
            ).also {
                if (it.equals(Pointer.NULL)) throw java.io.IOException("could not open process $processId")
            }
        }
    }

    val pid: Int get() = processId

    fun readBytes(address: Long, size: Int): ByteArray? {
        val buffer = Memory(size.toLong())
        val bytesRead = IntByReference()
        val ok = Win32.kernel32.ReadProcessMemory(handle, Pointer(address), buffer, size, bytesRead)
        if (!ok) return null
        return buffer.getByteArray(0, size)
    }

    fun readInt(address: Long): Int? {
        val b = readBytes(address, 4) ?: return null
        return (b[0].toInt() and 0xFF) or
            ((b[1].toInt() and 0xFF) shl 8) or
            ((b[2].toInt() and 0xFF) shl 16) or
            ((b[3].toInt() and 0xFF) shl 24)
    }

    fun readFloat(address: Long): Float? {
        val b = readBytes(address, 4) ?: return null
        val bits = (b[0].toInt() and 0xFF) or
            ((b[1].toInt() and 0xFF) shl 8) or
            ((b[2].toInt() and 0xFF) shl 16) or
            ((b[3].toInt() and 0xFF) shl 24)
        return Float.fromBits(bits)
    }

    fun readBool(address: Long): Boolean? {
        val b = readBytes(address, 1) ?: return null
        return b[0].toInt() != 0
    }

    /** Port of `pymem.read_string` (null-terminated, at most `byte` chars). */
    fun readString(address: Long, byte: Int = 50): String? {
        val b = readBytes(address, byte) ?: return null
        val end = b.indexOf(0).takeIf { it >= 0 } ?: b.size
        return String(b, 0, end, Charsets.UTF_8)
    }

    fun writeFloat(address: Long, value: Float): Boolean {
        val buffer = Memory(4)
        val bits = value.toBits()
        buffer.setByte(0, (bits and 0xFF).toByte())
        buffer.setByte(1, ((bits shr 8) and 0xFF).toByte())
        buffer.setByte(2, ((bits shr 16) and 0xFF).toByte())
        buffer.setByte(3, ((bits shr 24) and 0xFF).toByte())
        val bytesWritten = IntByReference()
        return Win32.kernel32.WriteProcessMemory(handle, Pointer(address), buffer, 4, bytesWritten)
    }

    fun close() {
        synchronized(openHandles) {
            if (openHandles.remove(processId) == handle) {
                runCatching { Win32.kernel32.CloseHandle(handle) }
            }
        }
    }
}
