package com.ghostbot.lib

import com.ghostbot.mapNavigation.Zone
import kotlin.math.abs
import kotlin.math.ceil
import kotlin.math.floor
import kotlin.math.hypot

/**
 * Port of GhostBot/lib/math.py.
 *
 * Position helpers mirror the Python exactly (including the "dumb, and wrong"
 * `pos` rounding the Talisman Online client does).
 */

private fun pos(a: Double): Double = if (a < 0) a * -1 else a

  /** Distance between 2 coordinates in a direct line, floored to int. */
fun linearDistance(a: Pair<Number, Number>, b: Pair<Number, Number>): Int =
    floor(hypot(pos(a.first.toDouble() - b.first.toDouble()), pos(a.second.toDouble() - b.second.toDouble()))).toInt()

/** `(100, 10) - (70, 7) == (30, 3)` */
fun positionDifference(a: Pair<Double, Double>, b: Pair<Double, Double>): Pair<Double, Double> =
    (a.first - b.first) to (a.second - b.second)

/** Clamp [number] to [-limit, limit]. */
fun limit(number: Double, limitValue: Double): Double =
    if (number < 0) {
        if (number < limitValue * -1) limitValue * -1 else number
    } else {
        if (number > limitValue) limitValue else number
    }

/** World coords -> map screen coords, mirroring the Python's hardcoded 1024x768. */
fun coordsToMapScreenPos(zone: Zone, targetCoords: Pair<Double, Double>): Pair<Int, Int> {
    val centre = zone.centre.first.toDouble() to zone.centre.second.toDouble()
    val diff = positionDifference(centre, targetCoords)
    return (1024.0 / 2 + diff.first / zone.scale.first).toInt() to
        (768.0 / 2 + diff.second / zone.scale.second).toInt()
}

/** ((hours * 60) + minutes) * 60 + seconds + tenths/10 */
fun seconds(hours: Int = 0, minutes: Int = 0, sec: Int = 0, tenths: Double = 0.0): Double =
    ((hours * 60) + minutes) * 60.0 + sec + tenths / 10.0

/** Screen location of an inventory/sell item given its sequence number and the top-left slot. */
fun itemCoordinatesFromPos(pos: Int, basePos: Pair<Int, Int>? = null): Pair<Int, Int> {
    val multiplier = 35
    val p = (floor(pos / 6.0).toInt() * multiplier) to ((pos % 6) * multiplier)
    return basePos?.let { (it.first + p.first) to (it.second + p.second) } ?: p
}

const val MAX_MINIMAP_MOVE = 30

   /** Cap the minimap click distance to a 30-pixel radius around the minimap centre. */
fun scaleMinimapMoveDistance(p: Pair<Number, Number>): Pair<Int, Int> {
    val pd = p.first.toDouble() to p.second.toDouble()
    if (linearDistance(pd, 0.0 to 0.0) <= MAX_MINIMAP_MOVE) {
        return pd.first.toInt() to pd.second.toInt()
    }
    val mp = maxOf(abs(pd.first), abs(pd.second))
    val ratio = mp / MAX_MINIMAP_MOVE
    return roundCoordinates(pd.first / ratio to pd.second / ratio)
}

fun roundCoordinates(p: Pair<Double, Double>): Pair<Int, Int> =
    (if (p.first >= 0) ceil(p.first) else floor(p.first)).toInt() to
        (if (p.second >= 0) ceil(p.second) else floor(p.second)).toInt()
