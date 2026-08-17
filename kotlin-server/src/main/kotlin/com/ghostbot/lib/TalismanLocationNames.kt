package com.ghostbot.lib

/**
 * Port of GhostBot/lib/talisman_location_names.py.
 * (Marked "FIXME: DETETE, UNUSED" upstream, but covered by the test suite.)
 */
/**
 * Map a world coordinate to a rough location name.
 */
fun locationToName(location: Pair<Int, Int>): String? {
    val (x, y) = location
    if (70 < x && x < 500 && y < -250 && y > -780) return "Stone City"
    if (500 < x && x < 1520 && y < -270 && y > -770) return "Vast Mountain"
    if (1520 < x && x < 3100 && y < 0 && y > -770) return "Dai's Field"
    return null
}
