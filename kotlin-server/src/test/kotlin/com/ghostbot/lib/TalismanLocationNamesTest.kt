package com.ghostbot.lib

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test

/** Port of tests/test_talisman_location_names.py. */
class TalismanLocationNamesTest {

    @Test
    fun `location to name`() {
        assertEquals("Stone City", locationToName(285 to -509))
        assertEquals("Vast Mountain", locationToName(895 to -500))
        assertEquals("Dai's Field", locationToName(2594 to -316))
        assertNull(locationToName(0 to 0))
    }
}
