package com.ghostbot.lib

import com.ghostbot.rootLogger

/**
 * Port of GhostBot/lib/vk_codes.py — VK key codes and `get_with_case`.
 */
object VkCodes {
    val codes: Map<Any, Int> = buildMap {
        put("backspace", 0x08); put("BACKSPACE", 0x08)
        put("tab", 0x09); put("TAB", 0x09)
        put("clear", 0x0C)
        put("enter", 0x0D); put("ENTER", 0x0D)
        put("shift", 0x10); put("ctrl", 0x11); put("alt", 0x12)
        put("pause", 0x13); put("caps_lock", 0x14)
        put("esc", 0x1B); put("spacebar", 0x20); put(" ", 0x20)
        put("page_up", 0x21); put("page_down", 0x22)
        put("end", 0x23); put("home", 0x24)
        put("left_arrow", 0x25); put("up_arrow", 0x26)
        put("right_arrow", 0x27); put("down_arrow", 0x28)
        put("select", 0x29); put("print", 0x2A); put("execute", 0x2B)
        put("print_screen", 0x2C); put("ins", 0x2D); put("del", 0x2E); put("help", 0x2F)
        for (i in 0..9) {
            put(i, 0x30 + i)
            put(i.toString(), 0x30 + i)
        }
        for (i in 'a'..'z') put(i.toString(), 0x41 + (i - 'a'))
        put("numpad_0", 0x60)
        for (i in 1..9) put("numpad_$i", 0x60 + i)
        put("multiply_key", 0x6A); put("add_key", 0x6B); put("separator_key", 0x6C)
        put("subtract_key", 0x6D); put("decimal_key", 0x6E); put("divide_key", 0x6F)
        for (i in 1..24) {
            put("F$i", 0x70 + i - 1)
            put("f$i", 0x70 + i - 1)
        }
        put("num_lock", 0x90); put("scroll_lock", 0x91)
        put("left_shift", 0xA0); put("right_shift ", 0xA1)
        put("left_control", 0xA2); put("right_control", 0xA3)
        put("left_menu", 0xA4); put("right_menu", 0xA5)
        put("browser_back", 0xA6); put("browser_forward", 0xA7)
        put("browser_refresh", 0xA8); put("browser_stop", 0xA9)
        put("browser_search", 0xAA); put("browser_favorites", 0xAB)
        put("browser_start_and_home", 0xAC)
        put("volume_mute", 0xAD); put("volume_Down", 0xAE); put("volume_up", 0xAF)
        put("next_track", 0xB0); put("previous_track", 0xB1)
        put("stop_media", 0xB2); put("play/pause_media", 0xB3)
        put("start_mail", 0xB4); put("select_media", 0xB5)
        put("start_application_1", 0xB6); put("start_application_2", 0xB7)
        put("attn_key", 0xF6); put("crsel_key", 0xF7); put("exsel_key", 0xF8)
        put("play_key", 0xFA); put("zoom_key", 0xFB); put("clear_key", 0xFE)
        put("+", 0xBB); put(",", 0xBC); put("-", 0xBD); put(".", 0xBE); put("/", 0xBF)
        put(";", 0xBA); put("[", 0xDB); put("\\", 0xDC); put("]", 0xDD)
        put("'", 0xDE); put("`", 0xC0)
    }

    private val logger = java.util.logging.Logger.getLogger("GhostBot.VkCodes")

    /** Port of `get_with_case`: fetch the keycode for [key]. */
    fun getWithCase(key: Any?): Int {
        val code = when {
            key is String && key.length == 1 -> {
                val lower = key.lowercase()
                val base = codes[lower] ?: codes[key] ?: throwKeyError(key)
                if (key == key.uppercase() && key != key.lowercase()) base + 0x20 else base
            }
            else -> codes[key] ?: throwKeyError(key)
        }
        return code
    }

    private fun throwKeyError(key: Any?): Nothing {
        logger.severe("vk_codes.py :: INTERNAL ERROR: $key not found in vk_codes")
        throw NoSuchElementException("$key not found in vk_codes")
    }
}
