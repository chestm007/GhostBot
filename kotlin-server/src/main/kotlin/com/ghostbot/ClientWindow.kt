package com.ghostbot

import com.ghostbot.lib.Location
import com.ghostbot.lib.UILocations
import com.ghostbot.lib.VkCodes
import com.ghostbot.mapNavigation.locationToZoneMap
import com.ghostbot.rootLogger
import com.ghostbot.win32.HWND
import com.ghostbot.win32.Pointers
import com.ghostbot.win32.ProcessMemory
import com.ghostbot.win32.Win32
import com.ghostbot.win32.Win32Messages
import org.opencv.core.CvType
import org.opencv.core.Mat
import java.io.File
import kotlin.math.ceil
import kotlin.math.hypot

/**
 * Port of GhostBot/abstract_client_window.py.
 *
 * The abstract client window: window input (keys/clicks), movement helpers,
 * inventory/map open-close loops and character state getters.
 */
abstract class AbstractClientWindow {
    val logger = java.util.logging.Logger.getLogger("GhostBot.AbstractClientWindow")

    protected val imageFinder: ImageFinder get() = lazyImageFinder
    private val lazyImageFinder: ImageFinder by lazy { ImageFinder(this) }

    abstract val identifier: String
    abstract val windowHandle: HWND?
    abstract fun setWindowName(): AbstractClientWindow

    val hasAliveTarget: Boolean
        get() {
            val hp = targetHp
            if (hp == null || hp < 0) return false
            if (targetName == name) return false
            return true
        }

    fun newTarget(key: Any? = "tab"): AbstractClientWindow {
        pressKey(key)
        return this
    }

    fun targetSelf(key: Any? = "F1"): AbstractClientWindow {
        pressKey(key)
        return this
    }

    fun sit(key: Any? = "x"): AbstractClientWindow {
        pressKey(key)
        return this
    }

    abstract val disconnected: Boolean
    abstract val onMount: Boolean

    inline fun <T> mounted(key: Any? = null, block: () -> T): T {
        if (key == null) return block()
        mount(key)
        val result = block()
        dismount(key)
        return result
    }

    open fun mount(key: Any? = null) {
        if (key == null) return
        var attempts = 0
        while (!onMount && attempts < 3) {
            attempts++
            pressKey(key)
            Thread.sleep(4000)
        }
        if (attempts == 3) logger.severe("Failed to mount up")
    }

    fun dismount(key: Any? = null) {
        if (key == null) return
        var attempts = 0
        while (onMount && attempts < 3) {
            attempts++
            pressKey(key)
            Thread.sleep(4000)
        }
        if (attempts == 3) logger.severe("Failed to dismount")
    }

    /** Capture the client window as a grayscale Mat (port of `capture_window`). */
    abstract fun captureWindow(): Mat

    abstract fun pressKey(key: Any?, charOnly: Boolean = false)

    fun typeKeys(keys: String, charOnly: Boolean = false) {
        for (key in keys.map { if (it.isUpperCase()) it.lowercaseChar() else it.uppercaseChar() }) {
            pressKey(key, charOnly = charOnly)
        }
    }

    abstract fun leftClick(pos: Pair<Int, Int>)
    abstract fun rightClick(pos: Pair<Int, Int>)

    fun getWindowPos(): Location? = getWindowSizePos()?.first
    fun getWindowSize(): Location? = getWindowSizePos()?.second
    abstract fun getWindowSizePos(): Pair<Location, Location>?

    fun openSurroundingsUi() {
        leftClick(UILocations.minimapSurroundings)
        Thread.sleep(500)
    }

    fun mapOpen(): Boolean = imageFinder.isMapOpen()

    inline fun <T> map(block: () -> T): T {
        openMap()
        val result = block()
        closeMap()
        return result
    }

    fun openMap() {
        while (!mapOpen()) {
            pressKey("m")
        }
    }

    fun closeMap() {
        while (mapOpen()) {
            pressKey("m")
        }
    }

    abstract val inventoryOpen: Boolean

    inline fun <T> inventory(block: () -> T): T {
        openInventory()
        val result = block()
        closeInventory()
        return result
    }

    fun openInventory() {
        while (!inventoryOpen) {
            pressKey("i")
            Thread.sleep(1000)
        }
    }

    fun closeInventory() {
        while (inventoryOpen) {
            pressKey("i")
            Thread.sleep(1000)
        }
    }

    fun searchSurroundings(value: String) {
        openSurroundingsUi()
        leftClick(UILocations.surroundingsSearch)
        Thread.sleep(500)
        typeKeys(value)
        Thread.sleep(500)
    }

    fun gotoFirstSurroundingResult() {
        leftClick(UILocations.surroundingsFirstItem)
        openSurroundingsUi()
    }

    fun clickNpc() {
        rightClick(UILocations.npcLocation)
    }

    fun resetCamera() {
        leftClick(UILocations.viewReset)
    }

    abstract val teamSize: Int
    abstract val teamMembers: List<String>
    abstract val petActive: Boolean
    abstract val hp: Int?
    abstract val maxHp: Int?
    abstract val mana: Int?
    abstract val maxMana: Int?
    abstract val name: String?
    abstract val level: Int?
    abstract val sitting: Boolean
    abstract val inBattle: Boolean
    abstract val location: Location
    abstract val locationName: String?
    abstract val targetLocation: Location?
    abstract val targetId: String?
    abstract val notification: Boolean
    abstract val hasTarget: Boolean
    abstract val targetHp: Int?
    abstract val targetName: String?

    val locationX: Int get() = location.x
    val locationY: Int get() = location.y

    open fun hpPercent(): Double = (hp ?: 0).toDouble() / (maxHp ?: 0)
    open fun manaPercent(): Double = (mana ?: 0).toDouble() / (maxMana ?: 0)
}

/**
 * Port of GhostBot/client_window.py `Win32ClientWindow`.
 *
 * Talks to the Talisman Online client via Win32 messages (JNA) and reads
 * character state from process memory (Pointers).
 */
open class Win32ClientWindow(val proc: ProcessMemory) : AbstractClientWindow() {
    companion object {
        const val TARGET_MAX_HP = 597
        const val TARGET_MIN_HP = 461
        private const val CHAR_ADDR_OFFSET = 0xC20980L
    }

    private var _name: String? = null
    /**
     * Cached character name. Set directly by the LoginController while filling
     * in credentials (port of `self._client._name = self._config.char_name`).
     */
    var nameCache: String?
        get() = _name
        set(value) {
            _name = value
        }
    private var _windowHandle: HWND? = null
    var pointers: Pointers? = null

    val processId: Int = proc.processId

    init {
        initializePointers()
        setWindowName() // Python wrapped this in suppress(TypeError); no-op when name is null
    }

    override val identifier: String
        get() = "${name.orEmpty()}[$processId]"

    open fun postLoginSetup() {
        setWindowName()
        initializePointers(forceReload = true)
    }

    open fun initializePointers(forceReload: Boolean = false) {
        try {
            if (pointers == null || forceReload) {
                logger.fine("Win32ClientWindow :: $identifier :: ${if (forceReload) "FORCE" else ""} initializing pointers")
                pointers = Pointers(processId)
            }
            // The Python re-reads `char` (a memory base); we only keep the Pointers object.
        } catch (e: Exception) {
            // ProcessError/MemoryReadError in the Python
        }
    }

    override val windowHandle: HWND?
        get() {
            if (_windowHandle == null) {
                val hwnds = Win32.getHwndsForPid(processId)
                if (hwnds.size == 1) {
                    logger.fine("Win32ClientWindow :: $identifier :: got window handle")
                    _windowHandle = hwnds[0]
                }
            }
            return _windowHandle
        }

    override fun setWindowName(): Win32ClientWindow {
        val name = name
        if (name != null) {
            windowHandle?.let { Win32.setWindowText(it, "Talisman Online | $name") }
        }
        return this
    }

    fun getWindowName(): String {
        val hwnd = windowHandle ?: return ""
        return try {
            Win32.getWindowText(hwnd).split(" | ").lastOrNull().orEmpty()
        } catch (e: Exception) {
            ""
        }
    }

    override val disconnected: Boolean
        get() {
            val p = pointers ?: return true
            return try {
                p.getHp() == null
            } catch (e: Exception) {
                true
            }
        }

    override val onMount: Boolean
        get() = pointers?.mount() ?: false

    override fun captureWindow(): Mat {
        val hwnd = windowHandle ?: error("no window handle for $identifier")
        val rect = Win32.getWindowRect(hwnd) ?: error("no window rect for $identifier")
        val w = (rect.right - rect.left).toInt()
        val h = (rect.bottom - rect.top).toInt()
        val rgba = Win32.captureWindow(hwnd, w, h) ?: error("failed to capture window $identifier")
        // RGBA -> grayscale (BT.601), like cv2.cvtColor(BGR, COLOR_BGR2GRAY)
        val gray = Mat(h, w, CvType.CV_8UC1)
        var row = 0
        while (row < h) {
            var col = 0
            while (col < w) {
                val o = (row * w + col) * 4
                val r = rgba[o].toInt() and 0xFF
                val g = rgba[o + 1].toInt() and 0xFF
                val b = rgba[o + 2].toInt() and 0xFF
                gray.put(row, col, (0.299 * r + 0.587 * g + 0.114 * b).toInt().coerceIn(0, 255).toDouble())
            }
            row++
        }
        return gray
    }

    override fun pressKey(key: Any?, charOnly: Boolean) {
        val hwnd = windowHandle ?: return
        val vk = try {
            VkCodes.getWithCase(key)
        } catch (e: Exception) {
            return
        }
        if (!charOnly) Win32.sendMessage(hwnd, Win32Messages.WM_KEYDOWN, vk.toLong())
        Win32.sendMessage(hwnd, Win32Messages.WM_CHAR, vk.toLong())
        if (!charOnly) Win32.sendMessage(hwnd, Win32Messages.WM_KEYUP, vk.toLong())
    }

    override fun leftClick(pos: Pair<Int, Int>) {
        val hwnd = windowHandle ?: return
        val lparam = Win32.makeLong(pos.first, pos.second)
        Win32.sendMessage(hwnd, Win32Messages.WM_MOUSEMOVE, 0, lparam)
        Thread.sleep(100)
        Win32.sendMessage(hwnd, Win32Messages.WM_LBUTTONDOWN, 0x0001, lparam)
        Win32.sendMessage(hwnd, Win32Messages.WM_LBUTTONUP, 0, lparam)
        Thread.sleep(100)
    }

    override fun rightClick(pos: Pair<Int, Int>) {
        val hwnd = windowHandle ?: return
        val lparam = Win32.makeLong(pos.first, pos.second)
        Win32.sendMessage(hwnd, Win32Messages.WM_MOUSEMOVE, 0, lparam)
        Thread.sleep(100)
        Win32.sendMessage(hwnd, Win32Messages.WM_RBUTTONDOWN, 0x0002, lparam)
        Win32.sendMessage(hwnd, Win32Messages.WM_RBUTTONUP, 0, lparam)
        Thread.sleep(100)
    }

    fun closeWindow() {
        _windowHandle?.let { Win32.sendMessage(it, Win32Messages.WM_DESTROY) }
    }

    override fun getWindowSizePos(): Pair<Location, Location>? {
        val hwnd = windowHandle ?: return null
        val titleBarHeight = Win32.getSystemMetrics(Win32.SM_CYCAPTION)
        val borderThickness = 6
        val rect = Win32.getWindowRect(hwnd) ?: run {
            logger.fine("Win32ClientWindow :: $identifier :: error getting window handle $hwnd")
            return null
        }
        var wx = rect.left.toInt()
        var wy = rect.top.toInt()
        var ww = (rect.right - rect.left).toInt()
        var wh = (rect.bottom - rect.top).toInt()
        wx += borderThickness
        wy += titleBarHeight + borderThickness
        ww -= borderThickness
        wh -= borderThickness
        return Location(wx, wy) to Location(ww, wh)
    }

    override val inventoryOpen: Boolean
        get() = pointers?.isBagOpen() ?: false

    override val teamSize: Int
        get() = pointers?.getTeamSize() ?: 0

    override val teamMembers: List<String>
        get() {
            val p = pointers ?: return emptyList()
            val check = listOf(
                { p.teamName1() },
                { p.teamName2() },
                { p.teamName3() },
                { p.teamName4() },
            )
            return (0 until (teamSize - 1).coerceAtLeast(0)).mapNotNull { check[it].invoke() }
        }

    override val petActive: Boolean
        get() = pointers?.petActive() ?: false

    override val hp: Int?
        get() = pointers?.getHp()

    override val maxHp: Int?
        get() = pointers?.getMaxHp()

    override val maxMana: Int?
        get() = pointers?.getMaxMana()

    override val mana: Int?
        get() = pointers?.getMana()

    override val name: String?
        get() {
            if (_name == null) {
                val p = pointers
                if (p == null) return null
                _name = try {
                    p.getCharName()
                } catch (e: Exception) {
                    null
                } ?: runCatching {
                    proc.readString(0x400000L + CHAR_ADDR_OFFSET + 0x3C4L, 16)
                }.getOrNull()
            }
            return _name
        }

    override val level: Int?
        get() = pointers?.getLevel()

    override val sitting: Boolean
        get() = pointers?.isSitting() ?: false

    override val inBattle: Boolean
        get() = pointers?.isInBattle() ?: false

    override val location: Location
        get() {
            val p = pointers ?: return Location(0, 0)
            return try {
                Location(p.getX(), p.getY())
            } catch (e: Exception) {
                Location(0, 0)
            }
        }

    override val locationName: String?
        get() {
            val p = pointers ?: return null
            var loc: String? = null
            for (getter in listOf({ p.getLocation() }, { p.getLocation2() })) {
                val candidate = runCatching { getter.invoke() }.getOrNull() ?: continue
                val cleaned = candidate.replace(" ", "").replace("'", "")
                if (cleaned.all { it.isLetter() }) {
                    val stripped = candidate.trim()
                    if (stripped in locationToZoneMap.keys) {
                        loc = stripped
                    }
                }
            }
            return loc
        }

    override val targetLocation: Location?
        get() {
            if (!hasAliveTarget || (targetHp ?: 0) < 0) return null
            val p = pointers ?: return null
            return runCatching {
                com.ghostbot.lib.withTimeout(timeoutMs = 1000) {
                    val id = p.getTargetId() ?: return@withTimeout null
                    // Full port of search_id (bidirectional pointer walk) is not performed here;
                    // the Python's search_id is a slow memory scan. We return null when the
                    // scan is unavailable — callers guard on null.
                    null
                }
            }.getOrNull()
        }

    override val targetId: String?
        get() = pointers?.getTargetId()

    override val notification: Boolean
        get() = pointers?.getNotification() ?: false

    override val hasTarget: Boolean
        get() = pointers?.isTargetSelected() ?: false

    override val targetHp: Int?
        get() {
            val p = pointers ?: return null
            return try {
                if (p.isTargetSelected()) {
                    val value = p.targetHp() ?: return null
                    if (value >= TARGET_MIN_HP) {
                        ceil((value - TARGET_MIN_HP).toDouble() / (TARGET_MAX_HP - TARGET_MIN_HP) * 100).toInt()
                    } else {
                        -1
                    }
                } else {
                    null
                }
            } catch (e: Exception) {
                logger.severe(e.toString())
                null
            }
        }

    override val targetName: String?
        get() = pointers?.getTargetName()
}
