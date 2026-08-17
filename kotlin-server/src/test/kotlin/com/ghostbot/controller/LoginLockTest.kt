package com.ghostbot.controller

import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Timeout
import java.util.concurrent.TimeUnit

/**
 * Port of the runnable parts of tests/test_login_controller.py that don't
 * require a live client window: the LoginLock class-level mutex semantics
 * (shared across instances, released after the block).
 */
@Timeout(30)
class LoginLockTest {

    @Test
    fun `lock locks and unlocks`() {
        LoginLock.release()
        assertFalse(LoginLock.locked)
        LoginLock.acquire("test_proc")
        try {
            assertTrue(LoginLock.locked)
        } finally {
            LoginLock.release()
        }
        assertTrue(LoginLock.unlocked)
    }

    @Test
    fun `withLock releases after the block`() {
        LoginLock.release()
        LoginLock.withLock {
            assertTrue(LoginLock.locked)
        }
        assertFalse(LoginLock.locked)
    }

    @Test
    fun `lock is shared across concurrent acquires`() {
        LoginLock.release()
        val holder = LoginLock.acquire("first")
        var secondAcquired = false
        val t = Thread {
            try {
                LoginLock.acquire("second", timeout = 0.5)
                secondAcquired = true
            } catch (e: java.util.concurrent.TimeoutException) {
                // expected: the first holder keeps the lock
            }
        }
        t.start()
        t.join(2000)
        assertFalse(secondAcquired, "second acquire should time out while first holds the lock")
        holder.release()
    }
}
