package com.ghostbot.lib

import java.io.FileNotFoundException
import java.util.concurrent.TimeoutException

/**
 * Port of the useful parts of GhostBot/lib/utils.py.
 */

/**
 * Port of `retry(func, retries, delay)` for zero-arg callables.
 * Returns true as soon as the callable returns true; sleeps `delay` seconds between tries.
 */
fun retry(func: () -> Boolean, retries: Int = 1, delay: Double = 1.0): Boolean {
    repeat(retries) {
        if (func()) return true
        sleepSeconds(delay)
    }
    return false
}

/**
 * Port of `retry` for callables that accept a `retry_count` parameter
 * (the Python inspects the signature for that kwarg and passes 1-based counts).
 */
fun retryWithCount(func: (retryCount: Int) -> Boolean, retries: Int = 1, delay: Double = 1.0): Boolean {
    for (i in 0 until retries) {
        if (func(i + 1)) return true
        sleepSeconds(delay)
    }
    return false
}

/**
 * Port of `with_timeout(func, timeout)`.
 * Runs [func] on a daemon thread and waits up to [timeoutMs] milliseconds.
 */
fun <T> withTimeout(timeoutMs: Long = 1000, func: () -> T): T {
  val holder = arrayOfNulls<Any?>(1)
  val done = java.util.concurrent.atomic.AtomicBoolean(false)
  val t = Thread({
      holder[0] = func()
      done.set(true)
  })
  t.isDaemon = true
  t.start()
  t.join(timeoutMs)
  if (!done.get()) throw TimeoutException("timed out after ${timeoutMs}ms")
  @Suppress("UNCHECKED_CAST")
  return holder[0] as T
}

fun sleepSeconds(d: Double) {
    if (d <= 0) return
    Thread.sleep((d * 1000).toLong())
}
