package com.ghostbot.win32

import com.ghostbot.rootLogger
import kotlin.math.floor

/**
 * Port of GhostBot/lib/talisman_online_python/pointers.py — Talisman Online
 * client memory pointers, on top of [ProcessMemory] instead of `pymem`.
 */
class Pointers(val processId: Int) {
    companion object {
        private val logger = java.util.logging.Logger.getLogger("GhostBot.Pointers")
    }

    private val pm = ProcessMemory(processId)

    // Ported pointer chain constants (from the Python Pointers.__init__).
    private val clientBase: Long = 0x400000L

    private val dcPointer = 0x012CE35CL
    private val charNamePointer = 0x011450ECL
    private val levelPointer = getPointer(clientBase + 0x00D450ECL, listOf(0x3C4L)) ?: 0L
    private val energyPointer = getPointer(clientBase + 0x00D450ECL, listOf(0x3CCL)) ?: 0L
    private val hpPointer = getPointer(clientBase + 0x00D450ECL, listOf(0x3B8L)) ?: 0L
    private val hpPlusPointer = getPointer(clientBase + 0x00D450ECL, listOf(0xE4L)) ?: 0L
    private val hpBuffPointer = getPointer(clientBase + 0x00D450ECL, listOf(0xE0L)) ?: 0L
    private val maxHpPointer = getPointer(clientBase + 0x00D450ECL, listOf(0xDCL)) ?: 0L
    private val goldPointer = getPointer(clientBase + 0x00D450ECL, listOf(0x410L)) ?: 0L

    private val manaPointer = getPointer(clientBase + 0x00D450ECL, listOf(0x3BCL)) ?: 0L
    private val manaBuffPointer = getPointer(clientBase + 0x00D450ECL, listOf(0x6F0L)) ?: 0L
    private val maxManaPointer = getPointer(clientBase + 0x00D450ECL, listOf(0x6ECL)) ?: 0L

    private val xPointer = getPointer(clientBase + 0x00D450ECL, listOf(0x810L)) ?: 0L
    private val yPointer = getPointer(clientBase + 0x00D450ECL, listOf(0x814L)) ?: 0L

    private val battleStatusPointer = getPointer(clientBase + 0x00D450ECL, listOf(0x854L)) ?: 0L
    private val sitPointer = getPointer(clientBase + 0x00D450ECL, listOf(0x290L)) ?: 0L

    private val targetHpPointer = getPointer(0x012CE2E0L, listOf(0x18L, 0x59CL, 0x0L, 0xCL, 0x1F4L, 0x15CL, 0x480L)) ?: 0L
    private val targetSelect = getPointer(clientBase + 0x00EC05C8L, listOf(0xD0L, 0x2DCL, 0x24L, 0xC10L)) ?: 0L
    private val targetNamePointer = getPointer(0x012CE2E0L, listOf(0x18L, 0xB1CL, 0x0L, 0xCL, 0x1F8L, 0x43CL)) ?: 0L
    private val targetNamePointer2 = getPointer(0x012CE2E0L, listOf(0x18L, 0xB1CL, 0x0L, 0xCL, 0xD9CL)) ?: 0L
    private val targetNamePointer3 = getPointer(0x012CE2E0L, listOf(0x18L, 0xB1CL, 0x0L, 0xCL, 0xD9CL, 0x9ACL)) ?: 0L

    private val teamSizePointer = getPointer(0x0106D328L, listOf(0x3D8L)) ?: 0L
    private val teamName1Ptr = getPointer(0x012CE2E0L, listOf(0x18L, 0x77CL, 0x0L, 0xCL, 0x678L, 0x8B4L)) ?: 0L
    private val teamName2Ptr = getPointer(0x012CE2E0L, listOf(0x18L, 0x34CL, 0x0L, 0xCL, 0x678L, 0x8B4L)) ?: 0L
    private val teamName3Ptr = getPointer(0x012CE2E0L, listOf(0x18L, 0x3F4L, 0x0L, 0xCL, 0x1F4L, 0x15CL)) ?: 0L
    private val teamName4Ptr = getPointer(0x012CE2E0L, listOf(0x18L, 0xA1CL, 0x0L, 0xCL, 0x1F4L, 0x54L)) ?: 0L

    private val bagOpenPointer = getPointer(0x012CE2E0L, listOf(0x18L, 0x5C4L, 0x0L, 0xCL, 0x1F8L, 0x42CL, 0xBA0L)) ?: 0L
    private val bag1 = getPointer(0x011450ECL, listOf(0x838L, 0xC4L, 0x0L, 0x8L, 0x10L)) ?: 0L
    private val bag2 = getPointer(0x011450ECL, listOf(0x838L, 0xC4L, 0x4L, 0x8L, 0x10L)) ?: 0L
    private val mountStatusPointer = getPointer(clientBase + 0x00D450ECL, listOf(0x8B0L)) ?: 0L

    private val petActivePointer = getPointer(0x11450ECL, listOf(0x10A8L)) ?: 0L

    private val lootPointer = getPointer(clientBase + 0x00EC05C8L, listOf(0xD0L, 0x7F4L, 0x0L, 0x24L, 0x40L)) ?: 0L
    private val lootWindow = 0x0105B958L

    private val firstLinkSur = getPointer(0x012CE2DCL, listOf(0x18L, 0x8CL, 0x3CL)) ?: 0L

    private val targetId = 0x115CB20L

    private val locationPointer = getPointer(0x011450ECL, listOf(0x7F8L, 0xF4L)) ?: 0L
    private val locationPointer2 = getPointer(0x011450ECL, listOf(0x7F8L, 0xF4L, 0x44CL)) ?: 0L
    private val notificationPointer = 0x0117097CL
    private val dialogPointer = getPointer(0x0117B27CL, listOf(0x70L, 0x56CL, 0xCL, 0x4L, 0x42CL, 0x1F8L, 0x240L)) ?: 0L
    private val confirmBoxPointer = 0x012CE35CL

    /**
     * Port of `Pointers.get_pointer` (the pymem monkey-patched version).
     * Chain: `address = base; for off in offsets: address = read_int(address) + off`.
     * The final address is NOT dereferenced.
     */
    fun getPointer(base: Long, offsets: List<Long>): Long? {
        return try {
            var address = base
            for (offset in offsets) {
                val cur = pm.readInt(address) ?: return null
                address = cur + offset
            }
            address
        } catch (e: Exception) {
            null
        }
    }

    private fun readIntOrNull(address: Long?): Int? =
        address?.let { pm.readInt(it) }

    private fun readInt(addr: Long): Int =
        pm.readInt(addr) ?: error("Pointers :: failed to read int at $addr")

    private fun readFloat(addr: Long): Float =
        pm.readFloat(addr) ?: error("Pointers :: failed to read float at $addr")

    /** Port of `read_string_from_pointer`. */
    private fun readStringFromPointer(basePointer: Long, offset: Long = 0, maxLength: Int = 50): String? {
       return try {
           val pointerAddress = pm.readInt(basePointer) ?: return null
           val finalAddress = pointerAddress + offset
           val byteData = pm.readBytes(finalAddress, maxLength) ?: return null
           val end = byteData.indexOf(0).takeIf { it >= 0 } ?: byteData.size
           val s = String(byteData, 0, end, Charsets.UTF_8)
           if (s.all { it.code < 128 }) s else null
       } catch (e: Exception) {
           null
       }
    }

    // ---------- getters (port of the Python methods) ----------

    fun getCharName(): String? {
        var name = readStringFromPointer(charNamePointer, offset = 0xBCL, maxLength = 50)
        if (name == null || name.all { it.isDigit() } || name.length < 5 || name.contains(' ')) {
            // alternate pointer for name
            val pointer = getPointer(clientBase + 0x00D450ECL, listOf(0xBCL))
            if (pointer != null) {
                name = readStringFromPointer(pointer, offset = 0x0L, maxLength = 50)
            }
        }
        return name
    }

    fun getTargetName(): String? {
       if (!isTargetSelected()) return null
       val isValid = { n: String? ->
           n != null && n.all { it.code < 128 } &&
               n.split(' ').all { it.isNotEmpty() && it.all { c -> c.isLetterOrDigit() } }
       }
       var name = readStringFromPointer(targetNamePointer3, offset = 0x0L, maxLength = 50)
       if (isValid(name)) return name
       name = readStringFromPointer(targetNamePointer, offset = 0x9ACL, maxLength = 50)
       if (isValid(name)) return name
       name = readStringFromPointer(targetNamePointer2, offset = 0x0L, maxLength = 50)
       if (isValid(name)) return name
       return null
    }

    fun teamName1(): String? = teamName(teamName1Ptr, 0x4F4L, listOf(0x18L, 0x77CL, 0x0L, 0xCL, 0x678L, 0x8B4L, 0x4F4L))
    fun teamName2(): String? = teamName(teamName2Ptr, 0x4F4L, listOf(0x18L, 0x34CL, 0x0L, 0xCL, 0x678L, 0x8B4L, 0x4F4L))
    fun teamName3(): String? = teamName(teamName3Ptr, 0x54L, listOf(0x18L, 0x3F4L, 0x0L, 0xCL, 0x1F4L, 0x15CL, 0x54L))
    fun teamName4(): String? = teamName(teamName4Ptr, 0x54L, listOf(0x18L, 0xA1CL, 0x0L, 0xCL, 0x1F4L, 0x54L, 0x54L))

    private fun teamName(base: Long?, offset: Long, fallbackOffsets: List<Long>): String? {
        if (base == null) return null
        var name = readStringFromPointer(base, offset = offset, maxLength = 50)
        if (name != null && Regex("^[\\w]+$").matches(name)) return name
        val pointer = getPointer(0x012CE2E0L, fallbackOffsets)
        if (pointer != null) {
            name = readStringFromPointer(pointer, offset = 0x0L, maxLength = 50)
        }
        return name
    }

    fun getLevel(): Int? = pm.readBytes(levelPointer, 1)?.first()?.toInt()

    fun getEnergy(): Int? = readIntOrNull(energyPointer)

    fun isTargetSelected(): Boolean {
        if (targetSelect == null) {
            logger.info("Pointers :: TARGET_SELECT pointer not calculated.")
            return false
        }
        return pm.readBytes(targetSelect, 1)?.first()?.toInt() == 1
    }

    fun targetHp(): Int? = readIntOrNull(targetHpPointer)

    fun petActive(): Boolean = pm.readBool(petActivePointer) ?: false

    fun targetHpFull(): Boolean = targetHp() == 597

    fun isTargetDead(): Boolean = targetHp() == 0

    fun getHp(): Int? = readIntOrNull(hpPointer)

    fun getHpPlus(): Int? {
        val plus = pm.readBytes(hpPlusPointer, 1)?.first()?.toInt() ?: return null
        return if (plus >= 100) plus - 100 else plus
    }

    fun getHpBuff(): Int? = readIntOrNull(hpBuffPointer)

    fun getMaxHp(): Int? {
        val baseHp = readIntOrNull(maxHpPointer) ?: return null
        val buffHp = getHpBuff() ?: return null
        val hpTotal = baseHp + buffHp
        val plus = getHpPlus() ?: return null
        return if (plus == 1) baseHp else floor(((hpTotal * plus) / 100.0) + hpTotal).toInt()
    }

    fun getMana(): Int? = readIntOrNull(manaPointer)

    fun getManaBuff(): Int? = readIntOrNull(manaBuffPointer)

    fun getMaxMana(): Int? {
        val baseMana = readIntOrNull(maxManaPointer) ?: return null
        val buffMana = getManaBuff() ?: return null
        return baseMana + buffMana
    }

    fun isInBattle(): Boolean = pm.readBytes(battleStatusPointer, 1)?.first()?.toInt() == 1

    fun isSitting(): Boolean = pm.readBytes(sitPointer, 1)?.first()?.toInt() == 200

    fun getX(): Int {
        val x = readFloat(xPointer) / 20f
        return if (x > 0) floor(x).toInt() else ceilToInt(x)
    }

    fun getY(): Int {
        val y = readFloat(yPointer) / 20f
        return if (y > 0) floor(y).toInt() else ceilToInt(y)
    }

    private fun ceilToInt(f: Float): Int = kotlin.math.ceil(f.toDouble()).toInt()

    fun isBagOpen(): Boolean = readIntOrNull(bagOpenPointer) == 903

    fun getTeamSize(): Int = readIntOrNull(teamSizePointer) ?: 0

    fun getDc(): Int? = readIntOrNull(dcPointer)

    fun getGold(): Int? = readIntOrNull(goldPointer)

    fun bag1Quantity(): Int? = readIntOrNull(bag1)

    fun bag2Quantity(): Int? = readIntOrNull(bag2)

    fun mount(): Boolean = (readIntOrNull(mountStatusPointer) ?: 0) != 0

    fun getTargetId(): String? {
        val id = readIntOrNull(targetId)
        if (id == null) {
            logger.info("Pointers :: error reading target id")
            return null
        }
        return id.toString(16).uppercase()
    }

    fun isLoot(): Int? = readIntOrNull(lootPointer)

    fun writePosition(pointer: Long, x: Double, y: Double): Boolean =
        pm.writeFloat(pointer + 0x810L, x.toFloat()) && pm.writeFloat(pointer + 0x814L, y.toFloat())

    fun lootWindow(): Boolean {
        val l = readIntOrNull(lootWindow) ?: return false
        return l == 1
    }

    /** Port of `get_sur_info` — parses `text="Name [x,y]"` from the surroundings list. */
    fun getSurInfo(): Map<String, String>? {
        val info = readStringFromPointer(firstLinkSur, offset = 0x64L, maxLength = 100) ?: return null
        val match = Regex("text=\"([^\"]+)\\s*\\[(-?\\d+),(-?\\d+)\\]\"").find(info) ?: return null
        return mapOf(
            "name" to match.groupValues[1].trim(),
            "coords" to "${match.groupValues[2]},${match.groupValues[3]}",
        )
    }

    fun confirmBox(): Boolean = readIntOrNull(confirmBoxPointer) == 1

    fun getLocation(): String? {
        val location = readStringFromPointer(locationPointer, offset = 0x44CL, maxLength = 100)
        if (location != null && Regex("^[\\w ']+$").matches(location)) {
            return location
        }
        val pointerAddress = pm.readInt(locationPointer) ?: return null
        val secondPointer = readStringFromPointer(pointerAddress + 0x44CL, offset = 0x0L, maxLength = 100)
        return secondPointer
    }

    fun getLocation2(): String? =
        readStringFromPointer(locationPointer2, offset = 0x0L, maxLength = 100)

    fun getNotification(): Boolean {
        val pointer = readIntOrNull(notificationPointer) ?: return false
        return pointer >= 1
    }

    fun getDialog(): Boolean = readIntOrNull(dialogPointer) == 16775

    fun getSystemMenu(): Boolean = readIntOrNull(0x012DC1F5L) == 1610612736

    fun close() {
        pm.close()
    }
}
