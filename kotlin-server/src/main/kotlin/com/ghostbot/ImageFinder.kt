package com.ghostbot

import com.ghostbot.rootLogger
import org.opencv.core.Core
import org.opencv.core.Mat
import org.opencv.imgcodecs.Imgcodecs
import org.opencv.imgproc.Imgproc
import java.io.File

/**
 * Port of GhostBot/image_finder.py — template matching on window captures.
 *
 * OpenCV native libraries are loaded at class init via the org.openpnp:opencv
 * dependency. On a host without the bundled native libs this throws
 * UnsatisfiedLinkError — the image-dependent tests skip themselves in that case.
 */
object ImageFinderCompanion {
    val miscFolder: String
    val imageFolder: String
    val items: Map<String, Mat>
    private val logger = java.util.logging.Logger.getLogger("GhostBot.ImageFinder")

    init {
        System.loadLibrary("opencv_java")
        val pathBase = System.getProperty("ghostbot.images.path")
            ?: System.getProperty("user.dir")
        var misc = File(pathBase, "GhostBot/Images/misc")
        if (!File(misc, "dialog_ok.bmp").exists()) {
            misc = File(pathBase, "Images/misc")
            if (!File(misc, "dialog_ok.bmp").exists()) {
                logger.severe("images not found in ${misc.path}")
                throw AssertionError("dialog_ok.bmp not found in misc_folder")
            }
        }
        miscFolder = misc.path

        var sell = File(pathBase, "Images/SELL")
        if (!File(sell, "greenid.bmp").exists()) {
            sell = File(pathBase, "Images/SELL")
            if (!File(sell, "greenid.bmp").exists()) {
                logger.severe(sell.path)
                throw AssertionError("greenid.bmp not found in image_folder")
            }
        }
        imageFolder = sell.path

        logger.info("Images path detected...")
        val loaded = mutableMapOf<String, Mat>()
        sell.listFiles()?.filter { it.isFile }?.forEach { file ->
            Imgcodecs.imread(file.path, Imgcodecs.IMREAD_GRAYSCALE)?.let { loaded[file.name] = it }
        }
        items = loaded
    }
}

class ImageFinder(private val client: AbstractClientWindow) {
    private val logger = java.util.logging.Logger.getLogger("GhostBot.ImageFinder")
    private var _destroyItemLocation: Pair<Long, Pair<Int, Int>?>? = null

    /** Port of the class-level `misc_folder` / `image_folder` / `items`. */
    companion object {
        /** Triggers native lib load + image discovery (port of the class-body discovery). */
        val miscFolder: String get() = ImageFinderCompanion.miscFolder
        val imageFolder: String get() = ImageFinderCompanion.imageFolder
        val items: Map<String, Mat> get() = ImageFinderCompanion.items
    }

    /**
     * Port of `_find_image_in_window`. Returns window-relative (x, y-30) or null.
     */
    private fun findImageInWindow(targetImage: Mat, threshold: Double = 0.8): Pair<Int, Int>? {
        val windowImg = client.captureWindow() ?: return null
        val result = Mat()
        Imgproc.matchTemplate(windowImg, targetImage, result, Imgproc.TM_CCOEFF_NORMED)
        val minMax = Core.minMaxLoc(result)
        val maxLoc = minMax.maxLoc
        if (minMax.maxVal > threshold) {
            return maxLoc.x.toInt() to (maxLoc.y.toInt() - 30)
        }
        return null
    }

    /** Port of `find_items_in_window`. */
    fun findItemsInWindow(itemImages: Map<String, Mat>): List<Pair<Int, Int>> {
        val toDelete = mutableListOf<Pair<Int, Int>>()
        val tolerance = 3

        val windowImg = client.captureWindow() ?: return toDelete
        val bagCoords = getBagCoords()
        if (bagCoords.isEmpty()) {
            logger.severe("ImageFinder :: getBagCoords :: bag_coords returned None")
            return toDelete
        }
        for (q in bagCoords) {
            val bagArea = Mat(windowImg, org.opencv.core.Rect(q.x1, q.y1, q.x2 - q.x1, q.y2 - q.y1))
            for ((_, itemImage) in itemImages) {
                val result = Mat()
                Imgproc.matchTemplate(bagArea, itemImage, result, Imgproc.TM_CCOEFF_NORMED)
                val threshold = 0.9
                // Python: np.where(result >= threshold)
                val mask = Mat()
                Core.compare(result, org.opencv.core.Scalar(threshold), mask, Core.CMP_GE)
                val coords = Mat()
                Core.findNonZero(mask, coords)
                for (row in 0 until coords.rows()) {
                    val pt = coords.get(row, 0)
                    val globalX = q.x1 + pt[0].toInt() + 10
                    val globalY = q.y1 + pt[1].toInt() - 15
                    val isDup = toDelete.any { existing ->
                        kotlin.math.abs(existing.first - globalX) <= tolerance &&
                            kotlin.math.abs(existing.second - globalY) <= tolerance
                    }
                    if (!isDup) {
                        toDelete.add(globalX to globalY)
                    }
                }
                result.release()
                mask.release()
                coords.release()
            }
            bagArea.release()
        }
        return toDelete
    }

    private fun fetchDestroyItemLocation(): Pair<Int, Int>? =
        findUiElement(File(miscFolder, "destroy-item.bmp").path, threshold = 0.8)

    val dialogOkLocation: Pair<Int, Int>?
        get() = findUiElement(File(miscFolder, "dialog_ok.bmp").path, threshold = 0.6)

    fun isMapOpen(): Boolean = findUiElement(File(miscFolder, "map_open.bmp").path) != null

    /** Port of `find_ui_element`. */
    fun findUiElement(bitmapPath: String, threshold: Double = 0.8): Pair<Int, Int>? {
        val image = Imgcodecs.imread(bitmapPath, Imgcodecs.IMREAD_GRAYSCALE)
        var found: Pair<Int, Int>? = null
        try {
            if (image.empty()) {
                logger.warning("ImageFinder :: ${client.identifier} :: image not found: $bitmapPath")
            } else {
                found = findImageInWindow(image, threshold)
            }
        } catch (e: Exception) {
            logger.severe("ImageFinder :: ${client.identifier} :: error in findImageInWindow")
            e.printStackTrace()
        } finally {
            image.release()
        }
        return found
    }

    /** Port of the `destroy_item_location` property (6s cache). */
    val destroyItemLocation: Pair<Int, Int>?
        get() {
            val current = _destroyItemLocation
            if (current == null || System.currentTimeMillis() - current.first > 6000) {
                _destroyItemLocation = System.currentTimeMillis() to fetchDestroyItemLocation()
            }
            return _destroyItemLocation?.second
        }

    /** Port of `_get_bag_coords`. */
    private fun getBagCoords(): List<Quad> {
        val destroyLocation = destroyItemLocation ?: run {
            logger.severe("ImageFinder :: getBagCoords :: destroy_item_location returned None")
            return emptyList()
        }
        val destroyX = destroyLocation.first
        val destroyY = destroyLocation.second
        return listOf(
            Quad(destroyX - 5, destroyY - 200, destroyX + 220, destroyY - 15),
            Quad(destroyX + 250, destroyY - 420, destroyX + 490, destroyY - 10),
        )
    }
}

private data class Quad(val x1: Int, val y1: Int, val x2: Int, val y2: Int)
