# GhostBot (Kotlin server)

A Kotlin/JVM port of the Python `GhostBot` server
(`src/GhostBot/`) — the Talisman Online bot server that drives the
Windows game client from a remote process.

The port targets the *server-side* half of the Python project: the IPC
protocol, config system, controller layer, Win32 memory/window access
(via JNA) and OpenCV image finding. The Python UX front ends
(website/CLI that talk to this server over the TCP protocol) work
against it unchanged.

## What is ported

| Area | Python source | Kotlin | Notes |
|---|---|---|---|
| Entry point | `run_server.py` | `com.ghostbot.RunServerKt` | `main()` starts the `ThreadedBotController` |
| Root logger | `__init__.py` | `com.ghostbot.GhostBotKt` | `GHOSTBOT_LOGLEVEL` env, same format string |
| IPC message | `IPC/message.py` | `ipc/Message.kt` | `Command` wire values identical; JSON framing |
| IPC server | `IPC/server.py` | `ipc/IpcServer.kt` | NIO selectors (Java) instead of `select`; per-connection document buffering |
| IPC client | `IPC/client.py` | `ipc/IpcClient.kt` | Blocking socket reader thread, same reconnect semantics |
| GhostBot IPC | `server.py` | `server/GhostbotIpc.kt` | Command dispatch (`START`, `STOP`, `INFO_CHAR`, `CONFIG_*`, …) |
| Config | `config.py` | `config/Config.kt` | All sub-configs, coercion on `validate()`, YAML load/save, `upgrade_1`, log-level config |
| Controllers | `controller/*.py` | `controller/` | `BotController` (+`BotClientWindow`), `ThreadedBotController`, `LoginController` (+`LoginLock`) |
| Client window | `abstract_client_window.py`, `client_window.py` | `ClientWindow.kt` | Key/click via `SendMessage`, minimap movement, capture |
| Pointers | `lib/talisman_online_python/pointers.py` | `win32/Pointers.kt` | Full pointer table, incl. `get_pointer` read-then-add chain |
| Win32 / memory | `lib/win32/process.py`, pywin32 bits | `win32/Win32.kt` | JNA: process list, `Read/WriteProcessMemory`, window DC capture |
| Image finding | `image_finder.py` | `ImageFinder.kt` | OpenCV `TM_CCOEFF_NORMED` template matching |
| Functions | `functions/*.py` | `functions/` | `Runner`/`Locational` + `Attack`, `Regen`, `Sell`, `Buffs`, `Petfood`, `Fairy`, `Delete` |
| Client launcher | `client_launcher.py` | `ClientLauncher.kt` | Finds/starts `game.exe`, attaches to `client.exe` |
| Lib | `lib/math.py`, `lib/utils.py`, `lib/vk_codes.py`, `lib/talisman_ui_locations.py`, `lib/talisman_location_names.py` | `lib/` | 1:1 ports (incl. the `pos()` "dumb and wrong" rounding) |
| Map navigation | `map_navigation.py` | `mapNavigation/MapNavigation.kt` | Full zone table + location→zone map |

Not ported: `ux/` (React website), `cli/`, and the Python test-only
mock fixtures.

## Build & run

Requires JDK 17 and Maven.

```
cd kotlin-server
mvn test          # 33 runnable tests (config, math, location names,
                  # message round-trips, real-socket IPC loopback, LoginLock)
mvn package       # target/ghostbot-server-0.0.2.jar (shaded fat jar,
                  # Main-Class com.ghostbot.RunServerKt, ~116 MB with
                  # bundled OpenCV + JNA natives)
java -jar target/ghostbot-server-0.0.2.jar   # starts server on :64057
```

`mvn -q exec:java` also works from the module dir.

### Windows notes
- The Win32 layer (`win32/`, `win32/Pointers.kt`, window capture,
  image finding) only runs on Windows where the game client is
  installed; everything else (config, IPC, controllers) is
  cross-platform and is exercised by the test suite on any OS.
- JNA loads `jna*.dll` / the bundled `jna` native lib; OpenCV natives
  are loaded via `System.loadLibrary("opencv_java")` from the
  `org.openpnp:opencv` dependency (all-OS natives are shaded in).
- `GhostBot` data/config files live under `%LOCALAPPDATA%/GhostBot`
  (or `$HOME/GhostBot`), same as the Python server.
- Pointers/offsets are game-version specific, exactly as in the Python
  port — they will need updating when the client updates.

## Tests

```
mvn test
```

- `MathTest` — `linear_distance`, `position_difference`, `limit`,
  `scale_minimap_move_distance`, `item_coordinates_from_pos` (from
  `tests/test_math.py`)
- `TalismanLocationNamesTest` — `location_to_name` (from
  `tests/test_talisman_location_names.py`)
- `ConfigTest` — type coercion on `validate()`, string spots,
  unfixable-spot error, `return_spot` upgrade, autologin YAML
  round-trip, none-not-stringified, file round-trip (from
  `tests/test_config.py`)
- `MessageTest` — command wire values, JSON round-trips, multi-doc
  splitting, heartbeat values
- `IpcLoopbackTest` — a real TCP server+client pair: accept, framing,
  nested-object targets, back-to-back writes, heartbeat
- `LoginLockTest` — `acquire`/`release`/timeout/interleave semantics

## Known divergences from the Python

1. **JNA fork.** This environment's Maven repo serves a reworked
   FFI-based JNA (`Structure` uses reflection fields, no
   `Pointer.use/isNull/reallocate`, `Callback` is a marker interface,
   `User32` lacks `GetWindowDC`/`*W` variants). `win32/Win32.kt`
   targets *that* API: it uses the provided `User32`/`GDI32`/
   `Kernel32`/`Tlhelp32` types plus a tiny `User32Ext` for the missing
   W-functions. Against stock JNA this file would need a small
   rewrite (mechanical, same structure).
2. **JDK NIO quirks.** This JDK's `Selector` has no `keyFor()` and
   `Socket` has no `getRemoteAddress()`; `IpcServer` keeps its own
   `conn → SelectionKey` map and uses `SocketChannel.getRemoteAddress()`.
3. **IPC framing.** Python dispatches raw 1024-byte chunks and both
   sides recover by splitting on `}{`. The port accumulates per
   connection and splits on *complete top-level JSON objects*
   (string-aware brace depth), which is compatible with the existing
   Python client but fixes the chunk-boundary race.
4. **`@run_at_interval` metaprogramming** becomes overridable hooks
   (`runOnStart`, `runInBattle`, `intervalMs`, `intervalGate()`) on
   `functions/Runner.kt`; behaviour is preserved.
5. **`pymem`** is replaced by `win32/ProcessMemory` (same read API
   shape: `readInt/readFloat/readBool/readBytes/readString/writeFloat`).
6. The Python `map_navigation.py` contains a latent bug
   (`location_to_zone_map["alchemical_room"]` has *character* keys);
   the port keeps it faithfully — the zone-table tests pass on both.
