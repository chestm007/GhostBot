package com.ghostbot.lib

/**
 * Port of GhostBot/lib/types.py `Location = namedtuple('Location', ['x', 'y'])`.
 */
data class Location(val x: Int, val y: Int) {
    fun toPair(): Pair<Double, Double> = x.toDouble() to y.toDouble()
}
