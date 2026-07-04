# GhostBot UI/UX Separation Cleanup Plan

## Goal
Remove UI/backend mixing in `src/GhostBot/UX` and the adjacent controller layer so the UI becomes a thin view layer and the game/automation logic lives in backend services.

## Problems identified
1. UI widgets directly talk to the game client and process/memory layer.
2. UI widgets contain business logic and file mutation.
3. Backend code emits UI-formatted strings and presentation details.
4. The main UI module is a god-object with too much state and formatting logic.
5. UI classes are tightly coupled to backend config dataclasses.
6. Autologin dialog has a callback cleanup bug.
7. Some backend serialization methods do more than serialize.

## Non-goals
- No visual redesign.
- No broad protocol rewrite.
- No changes to game behavior unless required by refactor.
- No attempt to “perfect” architecture in one pass.

## Working order
Start with the smallest, least risky changes and leave the structural cuts for last.

### Phase 1 — Safe hygiene fixes
Small edits that reduce coupling or remove obvious bugs without moving behavior.

1. Fix `autologin/main.py` callback cleanup bug:
   - replace the accidental `add_callback` with `del_callback`
   - convert debug `print()` calls to logger calls or remove them
2. Remove backend-owned display strings from `set_action(...)` call sites:
   - keep plain status text in backend
   - let UI decide emoji / styling
3. Clean obvious serialization noise:
   - trim `bot_controller.py:to_json()` to data gathering only where possible
4. Replace obvious `eval(...)` UI field reads with safe parsing helpers.

### Phase 2 — Isolate UI-to-game actions behind services
Move direct game-client interaction out of widgets.

5. Extract a service for map/spot capture used by:
   - `attack_frame.py`
   - `sell_frame.py`
6. Extract a service for “grab target” / position capture helpers if still embedded in widgets.
7. Remove direct `Win32ClientWindow` / `PymemProcess` construction from UI modules.
8. Keep UI callbacks, but make them call a backend service method instead of doing template matching or cursor math inline.

### Phase 3 — Reduce UI/business logic coupling
Move file edits, watchlist triage, and config logic out of widgets.

9. Move watchlist mutation and triage behavior out of `FunctionsFrame`.
10. Replace recursive widget-tree config extraction with an explicit registry or tab contract.
11. Stop UI tabs from depending directly on backend config dataclasses for all transformation logic.
12. Introduce a simple view-model boundary for UI state if the tab APIs become too wide.

### Phase 4 — Tidy the main UI composition
Refactor the main window after the lower-risk cuts are stable.

13. Split `UX/main.py` into:
   - app bootstrap
   - dashboard/status formatting
   - tab composition
   - IPC callback wiring
14. Move display formatting helpers out of the constructor and callback closures.
15. Reduce cross-thread UI callback work to a narrow update queue.

## Verification strategy
After each phase:
- run `python -m py_compile` on touched files
- run targeted tests or smoke commands if available
- search for the old coupling pattern to make sure it actually disappeared
- prefer small diffs with behavior preserved

## Acceptance criteria
The cleanup is “good enough” when:
- UI files no longer do process/memory/template-matching work directly
- backend files no longer emit presentation-specific strings
- config flow is explicit instead of widget-tree-driven
- the main UI module is mostly composition and callback wiring
- the obvious autologin bug is fixed

## Current status
- Audit complete.
- This plan is staged from low-risk to high-risk.
- Next implementation step should be Phase 1, item 1.
