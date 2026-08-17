package com.ghostbot

import java.text.SimpleDateFormat
import java.util.Date
import java.util.logging.Formatter
import java.util.logging.Handler
import java.util.logging.Level
import java.util.logging.LogRecord
import java.util.logging.Logger
import java.util.logging.StreamHandler

/**
 * Root logger configuration, mirrors GhostBot/__init__.py:
 * level taken from GHOSTBOT_LOGLEVEL env var (default INFO),
 * format "%(asctime)s: %(name)s: %(threadName)s: %(message)s".
 */
val rootLogger: Logger = Logger.getLogger("GhostBot")

private val ghostbotFormatter = object : Formatter() {
    override fun format(record: LogRecord): String {
        val asctime = SimpleDateFormat("yyyy-MM-dd HH:mm:ss,SSS").format(Date(record.millis))
        return "$asctime: ${record.loggerName}: ${Thread.currentThread().name}: ${record.message}"
    }
}

private var loggingConfigured = false

/** Configure the root logger once (idempotent). */
fun configureLogging() {
    if (loggingConfigured) return
    loggingConfigured = true
    val level = levelFromEnv()
    rootLogger.useParentHandlers = false
    // NOTE: this OpenJDK build's StreamHandler() default constructor does NOT
    // write to System.err (verified: records are dropped), so pass the stream
    // explicitly to keep logging working across JDK builds.
    val handler = StreamHandler(System.err, ghostbotFormatter)
    rootLogger.addHandler(handler)
    rootLogger.level = level
}

private fun levelFromEnv(): Level {
   val env = (System.getenv("GHOSTBOT_LOGLEVEL") ?: "INFO").uppercase()
   // java.util.logging.Level is not an enum — map by name.
   return when (env) {
       "SEVERE" -> Level.SEVERE
       "WARNING" -> Level.WARNING
       "INFO" -> Level.INFO
       "CONFIG" -> Level.CONFIG
       "FINE" -> Level.FINE
       "FINER" -> Level.FINER
       "FINEST" -> Level.FINEST
       "ALL" -> Level.ALL
       "OFF" -> Level.OFF
       else -> Level.INFO
   }
}
