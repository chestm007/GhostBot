package com.ghostbot.enums

/** Port of GhostBot/enums/bot_status.py `BotStatus`. */
enum class BotStatus(val value: Int) {
    CREATED(0),
    STARTING(1),
    STARTED(2),
    RUNNING(3),
    STOPPING(4),
    STOPPED(5),
    DISCONNECTED(6);

    companion object {
        fun fromValue(v: Int): BotStatus = entries.first { it.value == v }
    }
}
