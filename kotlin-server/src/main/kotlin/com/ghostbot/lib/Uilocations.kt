package com.ghostbot.lib

import com.ghostbot.lib.Location

/**
 * Port of GhostBot/lib/talisman_ui_locations.py.
 */
object UILocations {
    val player = 40 to 40
    val team1 = 30 to 200
    val team2 = 30 to 285
    val team3 = 30 to 365
    val team4 = 30 to 445
    val minimapCentre = 919 to 115
    val minimapSurroundings = 975 to 60
    val surroundingsSearch = 570 to 540
    val surroundingsFirstItem = 290 to 262
    val viewReset = 867 to 57
    val stall = 920 to 190
    val npcLocation = 500 to 395
    val sellItemSlot1 = 455 to 270
    val confirmSellButton = 475 to 713
    val charSelectEnterGame = 510 to 735
    val charSelectInterruptedOk = 510 to 333

    object ServerSelect {
        val whiteHorse = 380 to 245
        val blueIce = 380 to 265
        val wildWave = 380 to 285
        val giantSkyMetal = 380 to 305
        val tigerFish = 380 to 325
        val allStars = 380 to 345
        val lightInTheDarkness = 380 to 365
        val ok = 560 to 530

        val byName: Map<String, Pair<Int, Int>> = mapOf(
            "white_horse" to whiteHorse,
            "blue_ice" to blueIce,
            "wild_wave" to wildWave,
            "giant_sky_metal" to giantSkyMetal,
            "tiger_fish" to tigerFish,
            "all_stars" to allStars,
            "light_in_the_darkness" to lightInTheDarkness,
            "ok" to ok,
        )
    }
}

/** Port of `TeamLocations`. */
val TeamLocations: List<Pair<Int, Int>> =
    listOf(UILocations.player, UILocations.team1, UILocations.team2, UILocations.team3, UILocations.team4)
