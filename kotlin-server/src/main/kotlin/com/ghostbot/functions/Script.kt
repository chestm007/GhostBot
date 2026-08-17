package com.ghostbot.functions

import com.ghostbot.lib.Location
import org.yaml.snakeyaml.Yaml
import java.io.File

/** Port of GhostBot/functions/script.py. */

enum class ScriptAction(val value: Int) {
    MOVE(1),
    ATTACK(2);

    fun move(location: Location): ScriptStep<*> = ScriptStep(this, location)
    fun attack(target: String): ScriptStep<*> = ScriptStep(this, target)
}

class ScriptStep<T>(val action: ScriptAction, val parameters: T)

/**
 * A scripted sequence of steps.
 *
 * ```yaml
 * bc_bot:
 * - move [400, 65]
 * - move [375, 81]
 * ```
 */
class ScriptDefinition(val steps: List<ScriptStep<*>>) {
    companion object {
        private val yaml = Yaml()
        fun fromYaml(yamlFile: String): ScriptDefinition {
            val loaded = yaml.load<Any>(File(yamlFile).readText())
            @Suppress("UNCHECKED_CAST")
            return ScriptDefinition(loaded as List<ScriptStep<*>>)
        }
    }
}

class Script(client: com.ghostbot.controller.BotClientWindow) : Runner(client) {
    override fun _run(): Boolean? = null
}
