package com.ghostbot.lib

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

/** Port of tests/test_math.py. */
class MathTest {

    @Test
    fun `limit 0`() {
        assertEquals(0.0, limit(0.0, 20.0))
    }

    @Test
    fun `limit 0 to 20 passes through`() {
        for (i in 1 until 20) {
            assertEquals(i.toDouble(), limit(i.toDouble(), 20.0))
            assertTrue(i > 0)
        }
    }

    @Test
    fun `limit 20 to 400 clamps to 20`() {
        for (i in 20 until 400) {
            assertEquals(20.0, limit(i.toDouble(), 20.0))
        }
    }

    @Test
    fun `limit -20 to -1 passes through`() {
        for (i in -20 until -1) {
            assertEquals(i.toDouble(), limit(i.toDouble(), 20.0))
        }
    }

    @Test
    fun `limit -400 to -20 clamps to -20`() {
        for (i in -400 until -20) {
            assertEquals(-20.0, limit(i.toDouble(), 20.0))
        }
    }

    @Test
    fun `limit cherry pick`() {
        for (i in listOf(20, 40, 60, 100)) assertEquals(20.0, limit(i.toDouble(), 20.0))
        for (i in listOf(-20, -40, -60, -100)) assertEquals(-20.0, limit(i.toDouble(), 20.0))
        assertEquals(-10.0, limit(-10.0, 20.0))
        assertEquals(10.0, limit(10.0, 20.0))
    }

    @Test
    fun `position difference`() {
        assertEquals(10.0 to 10.0, positionDifference(10.0 to 10.0, 0.0 to 0.0))
        assertEquals(20.0 to 20.0, positionDifference(10.0 to 10.0, -10.0 to -10.0))
    }

    @Test
    fun `position difference negative`() {
        assertEquals(-10.0 to -10.0, positionDifference(-10.0 to -10.0, 0.0 to 0.0))
        assertEquals(-20.0 to -20.0, positionDifference(-10.0 to -10.0, 10.0 to 10.0))
    }

    @Test
    fun `seconds function`() {
        assertEquals(3600.0, seconds(hours = 1))
        assertEquals(60.0, seconds(minutes = 1))
        assertEquals(10.0, seconds(sec = 10))
        assertEquals(0.2, seconds(tenths = 2.0))
    }

    @Test
    fun `scale minimap move distance`() {
        assertEquals(10 to 10, scaleMinimapMoveDistance(10.0 to 10.0))
        assertEquals(-10 to 10, scaleMinimapMoveDistance(-10.0 to 10.0))
        assertEquals(30 to 30, scaleMinimapMoveDistance(70.0 to 70.0))
        assertEquals(-30 to -30, scaleMinimapMoveDistance(-70.0 to -70.0))
        assertEquals(-30 to 30, scaleMinimapMoveDistance(-70.0 to 70.0))
        assertEquals(30 to -30, scaleMinimapMoveDistance(70.0 to -70.0))
        assertEquals(13 to -30, scaleMinimapMoveDistance(30.0 to -70.0))
    }

    @Test
    fun `linear distance`() {
        assertEquals(0, linearDistance(10.0 to 10.0, 10.0 to 10.0))
        assertEquals(5, linearDistance(0.0 to 0.0, 3.0 to 4.0))
    }
}
