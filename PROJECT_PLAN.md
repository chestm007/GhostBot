# 📋 BotTO PROJECT — PLAN + STATUS

**Team:** 5 players (2 Fairy + 1 Wizard + 1 Tamer + 1 Assassin)
**Base:** Fork of `chestm007/GhostBot`, local branch `minha-versao-estavel`
**Stack:** Python 3.11+ on Windows 11 + Tesseract OCR + Cheat Engine + Discord Webhook + Tailscale
**Original schedule:** May 23 → August 12 (12 weeks + optional Sprint 6)
**Last doc update:** 2026-05-27

---

## 🔖 RESUME HERE — 2026-05-28 (session 5 — Sprint 7: Robust save DONE+VALIDATED; script list is next)

**Where we left off:** Started **Sprint 7 ("Bots ready"). PHASE 1 — Robust save: ✅ DONE and LIVE-VALIDATED (2026-05-28, "wonderful, saved it!!!").** Save no longer fails in SILENCE: the server now responds with success OR an `ERROR` with the reason, and the UI shows it **visibly** (green label "✓ Saved HH:MM:SS" / red popup + label on error). **PHASE 2 (next):** list of **scripts/presets** on the RIGHT side (mirrors the character list on the left) — "Save script" button, each item = name + `dd/mm/yy hh:mm`, click applies the preset to the selected char. **Owner's decision:** only allow switching scripts with the bot **STOPPED** (Stop = emergency). The 3 blocked items (need friends together) remain as PRIORITIES for later: Defender Bug 1, aggro from DPS in Cave Boss, distribute the `.exe`.

- 🔧 **ROBUST SAVE ✅ (Phase 1 of Sprint 7) — 2 files:**
  - `server.py` (`CONFIG_SET`): validation (`Config.load_yaml` → `validate()`) could throw `TypeError` and the dispatcher's `try/except` swallowed it → nothing saved, nothing warned. Now: char not found / invalid config / disk error → each responds `Message(Command.ERROR, {char, reason})` with the reason; success → confirms back.
  - `main.py`: status label next to Save (green success / red failure) + `Command.ERROR` callback that opens `messagebox.showerror` with the reason. Callback scheduled via `self.after(0,...)` (IPC callback runs on ANOTHER thread; tkinter is not thread-safe). Before there was no error callback at all.
  - ⚠️ Changed server AND UI → restart BOTH (closing the window is not enough; kill `ghost-bot-server`). The "Talisman Bot" icon starts both with the new code.
  - ℹ️ Tests: 39 pass; 4 failures are PRE-EXISTING (regen/config, leftover from Regen/Buff tab removal) — not introduced by this change, out of scope.

---

## 🔖 RESUME (session 4 — 2026-05-27) — Cave Boss Bot: 3 roles + pot cooldown

**Where we left off:** **Cave Boss Bot BUILT** — dynamic "Boss" tab (dropdown for role) with **3 roles (Tank/DPS/Fairy)**; "Boss only" rule (Boss on → rest blocked); 16s pot cooldown across the whole bot. **Still need owner to LIVE-VALIDATE the Boss** (said they'll test and give feedback). Before: Fairy Helper validated, client detection fixed. Open fronts: validate the Boss; Defender Bug 1 (PRIORITY when owner asks); distribute the `.exe`.

- 🐉 **CAVE BOSS BOT — 3 ROLES ✅ LIVE-VALIDATED (2026-05-27), only DPS aggro pending.** Spec in `CAVE_BOSS_BOT.md`. Boss tab = separate runner (`functions/boss.py` + `BossConfig`); role dropdown. **TANK ✅** (lock+combo+X buffs, no pots). **FAIRY ✅** (heal spam on current target). **DPS:** combat+MP ✅; **🔴 only AGGRO CONTROL is pending** (trigger = any HP drop → retreat; needs fine-tuning, likely threshold > X% so it doesn't retreat from light AoE). "Boss only Boss" rule in UI ✅.
- 💊 **POTS: 16s cooldown (global)** — pot in TO is regen over ~16s; the bot re-potted (duplicate pot). Fix in attack/boss/regen (`Runner._pot_ready/_use_pot`). Applies to normal farm too.
- 🧹 **REGEN and BUFF TABS REMOVED (2026-05-27, owner's decision):** Regen "useless" (you always pot in Attack); Buff was an empty shell. The **buff became a section in the Attack tab** ("Buffs every X min", `AttackConfig.buffs`/`buff_interval_mins`; `Attack._maybe_buff`). Tabs/checkboxes/loop-yields removed; `regen_frame.py`/`buff_frame.py` deleted. **KEPT** `regen.py`/`buffs.py` + `RegenConfig`/`BuffConfig` (tests + old .yml compat).
- 🧹 **FIELD ORDER STANDARDIZED (2026-05-27):** canonical order in all combat tabs — **Selector → Lock Boss+Name → Combo → HP/MP Pots → Buffs → Extras → Spot/movement**. The **Attack** was reordered (the "Lock onto Boss" moved to top, aligning with Boss which was already in order). Fairy/Pet/Sell have no common elements → kept as-is. (Only visual POSITION changed; behavior identical.)
- ⚔️ **ATTACK TAB GOT CLASS SELECTOR (DPS/Tamer/Fairy) (2026-05-27), to validate:** dropdown at top (same as Boss) that adds CLASS EXTRAS — combo stays generic. **DPS** (default) = current behavior intact (`char_class=None`). **Tamer**: "Pet attack key" field → bot commands pet to attack WHEN GRABBING each new target (`_command_pet`). **Fairy**: when "Pot HP at %" triggers, she presses the **heal key** (instead of HP pot — she heals herself); MP still via pot.
- 🐾 **PET REBUILT + ✅ LIVE-VALIDATED (2026-05-27) — TWO types, each with flag (owner's request):** `functions/petfood.py` + Pet tab redone (were empty shells). **(1) TAMER PET (combat)** [flag `tamer_pet`]: summons at Start, **re-summons if it dies** (detects `pet_active` each cycle), feeds every X min, optional periodic re-summon. **(2) NORMAL PET (companion)** [flag `normal_pet`]: only feeds every X min (own food `normal_food`). Fields for each block appear when the flag is checked. Pet combat = Attack tab (combo). ⏳ Pending confirmation: does the Tamer's pet attack on its own or needs a key in the combo? Does it expire on time (needs re-summon timer)?
- ✅ **Fairy self-heal CONFIRMED 100% live (2026-05-27):** Fairy's own HP < 50% → **F1 → heal → wait for cast → re-select 1st member → P**. Works. Note: `heal_self_threshold` has no UI field (`fairy_frame.py`) → falls to default 50% (`fairy.py:100`). Changing the threshold today requires code (not requested). **Fairy front CLOSED.**
- ✅ **CLIENT DETECTION BUG FIXED** (`controller/bot_controller.py:_scan_for_clients`): if the bot opened BEFORE the clients, they wouldn't appear in the list until restarting the bot. Cause: the scan shortcut skipped if the PID set didn't change — but a client opened on the login screen (name=None) has the same PID after logging in, so it was never re-evaluated. Fix: only skip scan if nothing changed **AND** every running process is already a client in the list (`all_registered`). **Live-validated** (opened bot → opened client later → appeared on its own). Test `test_async_bot_controller` passes.
- ⏪ **(05-26) ROOT BUG of "Fairy auto-selects itself" FIXED** (saga across MULTIPLE sessions): `get_with_case` in `lib/vk_codes.py` added `+0x20` to UPPERCASE letters → the 'follow' key `P`(0x50) became **`0x70 = F1 = auto-select itself`**. Fix: `return vk_codes[_key.lower()]` always. Live-validated.
- ⏪ **(05-26) Party member selection VALIDATED — all BACKSTAGE:** **F1** = self; **backstage click** (`left_click` from bot = SendMessage) = member. Coords `team_1..team_4` validated (1024x768; ~81px). ⚠️ **DO NOT use real mouse** (`SetCursorPos`) — owner's decision.
- 🧪 **FRIENDS TESTED the `.exe` package (2026-05-27) → 2 bugs reported (screenshots `Bug1.png`/`Bug2.png` in `OneDrive\\Desktop\\TO Bot\\`):**
  - 🔴 **BUG 1 (PRIORITY — RESOLVE WHEN OWNER ASKS):** the **UI doesn't open** on friend's machine — only the black server window (`run_server.exe`) opens; `run_client.exe` doesn't. Most likely cause: **Windows Defender blocks `run_client.exe` on execution** (Nuitka false-positive, ALREADY known — on owner's machine it was resolved with folder exclusion in Defender; friends don't have this). The `Iniciar BotTO.bat` checks if the file EXISTS (it does), but doesn't detect that Defender kills execution. Friend uses **standard Windows Defender**. ⏳ Waiting for friend's diagnosis (two clicks on `run_client.exe` → what appears). **DO NOT repackage yet** — accumulate changes first.
  - ✅ **BUG 2 (FIXED):** `Criar atalho do Talisman Bot.bat` failed with `DirectoryNotFoundException` when saving the shortcut — guessed `%USERPROFILE%\\Desktop`, which doesn't exist when OneDrive redirects the Desktop (default Win11). Fix: discover real Desktop via `[Environment]::GetFolderPath('Desktop')` (with fallback). Applied in both copies (repo + package folder). Didn't block (already had plan B), just scary.
- ▶️ **NEXT STEPS:** (1) owner **validates Cave Boss live** (will test and give feedback); (2) accumulate changes in package (Bug 1 + Boss + pots) BEFORE generating new `.exe`/zip; (3) when owner asks: tackle **Bug 1 (Defender)** and only then repackage + redistribute to friends.
- ⚠️ **Important:** the "Talisman Bot" icon (`start_botto.bat`) runs the console scripts (`ghost-bot-server.exe`/`ghost-bot-client.exe` from the Python folder) = **editable install = runs SOURCE live**. NOT the old `run_server.exe` from root. Clicking the icon ALREADY runs the new code.

---

## 📦 Previous session (2026-05-26 morning) — `.exe` package for friends

**Where we left off:** building the **`.exe` package for friends**. Server validated, client building.

- ✅ **`gh` CLI installed** (`winget install GitHub.cli`, v2.92.0) **and logged in** as `LpiresUrt` (repo+workflow scopes). Goes to `C:\\Program Files\\GitHub CLI\\gh.exe` (doesn't enter PATH automatically → `$env:Path += ';C:\\Program Files\\GitHub CLI'`). ⚠️ Repo has 2 remotes → **always `-R LpiresUrt/BotTO`** with `gh` (otherwise aims at upstream `chestm007` = HTTP 403). Now can trigger/download builds from the command line.
- ✅ **SERVER BUILD #2 = SUCCESS** (run `26450634537`, 15m16s, fix `43e4afb`). `run_server.exe` (55.7 MB) installed at `C:\\Bot\\BotTO` (build #1 → `.build1.bak`). **Smoke test passed:** log = `Images path detected...` + `Server listening...`, **no** `ModuleNotFoundError: pytesseract` from build #1. Images embedded + IPC OK.
  - 📥 **Artifact download:** `gh run download` FAILED (`archive: false` in workflow → artifact is the raw exe, not zip). Download via API: `Invoke-WebRequest .../actions/artifacts/<id>/zip -Headers @{Authorization="Bearer $(gh auth token)"}` (file comes with `MZ` signature = raw exe).
- 🔴 **DISCOVERY: Tesseract does NOT embed in `.exe`.** The nuitka (`--include-data-dir`/`--include-data-files`) **ignores `.dll`/`.exe`** on purpose → only `tessdata/` went into the binary, `tesseract.exe`+DLLs stayed out. Passed unnoticed on dev machine (falls to system Tesseract), but would break OCR on friend's machine.
  - ✅ **SOLUTION (validated):** Tesseract goes as FOLDER `Tesseract-OCR/` NEXT TO the `.exe` in the zip (not inside). The `_find_tesseract` already looks for `exe_folder/Tesseract-OCR/tesseract.exe` before fallback. For friend it's identical (extract, click, zero installation). **`run_server.exe` current already works** — no need to rebuild for this. Folder assembled with `python tools/make_portable_tesseract.py` (72 MB, runs standalone).
  - 🧹 TODO (non-blocking): remove the Tesseract embedding step from `build-executable.yml` (doesn't work, just inflates the .exe).
- ✅ **CLIENT BUILD OK** (run `26452436569`; 1st attempt Upload Artifact failed — transient — `gh run rerun --failed` fixed it). Smoke test passed.
- ⚠️ **Defender blocked `run_client.exe`** (Nuitka false-positive; server passed). Resolved with scoped exclusion in package folder (`C:\\Bot\\Talisman Bot`) + downgrade there. ⚠️ exclusion still active: `Remove-MpPreference -ExclusionPath "C:\\Bot\\Talisman Bot"` when no longer needed.
- ✅ **PACKAGE ASSEMBLED AND VALIDATED: `C:\\Bot\\Talisman Bot.zip` (139 MB).** Extraction tested (Explorer engine) = correct structure.
- ▶️ **NEXT STEP:**
  1. Owner uploads `Talisman Bot.zip` to a link (Drive/WeTransfer — 139 MB doesn't fit in Discord 25 MB) and sends to the 4 friends.
  2. **Validate OCR live** (pending): run `run_server.exe` from the package folder with the GAME open + farm → drop on panel/Discord = sibling-folder Tesseract OK.
  3. (Optional) remove the Tesseract embedding step from `build-executable.yml`; remove Defender exclusion.

**📦 PACKAGE FOR FRIENDS (`.exe` version — ZERO installation):**
Owner assembles and **sends the COMPLETE zip** to the 4 friends. Contents:
  - `run_server.exe` + `run_client.exe`
  - **`Tesseract-OCR/` folder** (next to the exes — drop OCR depends on it; ~72 MB)
  - `Images/`? NO — images (.bmp) are already embedded in the exes.
  - `Iniciar BotTO.bat` (opens server + UI with 1 click, requests admin) — local, gitignored
  - `LEIAME.txt` (instructions) — local, gitignored
  - `alertas_drop.txt` (default alert list)
  - ✅ **Owner's `discord_webhook.txt` SHARED** (decision 2026-05-26) → central feed; if leaked, delete+recreate.
  - Friends only need the **game installed** (official site). Don't open the server manually (the `.bat` starts both).
- 🎨 **ICONS:** the `.exe` already come with the logo (build embeds `logo.ico`). The `.bat` doesn't accept its own icon → include a **`Criar atalho do Talisman Bot.bat`** that friend runs once and generates a logo shortcut on their Desktop (shortcut `.lnk` made here breaks there due to absolute path).
- 🏷️ **Rename "GhostBot"?** Decided NOT to touch the internal name (package/imports, ~398×): high risk, zero visible gain. What friend sees is already "Talisman Bot" (title, logo, icon, LEIAME). Only semi-visible = config folder `~/GhostBot`.

---

## 📌 WHERE WE ARE NOW — QUICK SUMMARY (2026-05-24)

**Sprint 0 completed + big advance on sell/farm cycle and dashboard.** Bot runs, UI rebuilt (PT-BR gamer), and in this session the **full sell cycle was done and migrated to production**: navigate to NPC → sell → return to spot, all robust to window size/position.

### 🔥 Done in session 2026-05-24
- ✅ **TEMPLATE + OFFSET navigation** (anchor = panel title): Surroundings, NPC "Dialogue" window, sell dialog, map. Fixes broken fixed coords. Δ from title bar (capture=window coords, click=client coords) cancels with calibrated offset by cursor.
- ✅ **SELL CYCLE IN PRODUCTION** (`sell.py`): Surroundings → "Dialogue" → "Sell Item" → sells 3 bags (configurable starting slot, clicks 30× with reflow) → confirm → return to spot via map (decoy click to bypass game's repeated-click bug) → wait for arrival. Assembly via `mounted()`. Attack pauses/resumes on its own (sequential loop + run_at_interval).
- ✅ **Dashboard 100% working:** Target HP (fixed the oscillating `is_target_selected` gate), Mobs killed, Farm time, Energy, **XP gained (points)**, **Gold gained split into Gold/Silver/Copper**. Fixed 2 bugs that froze EVERYTHING: chars list repopulating every poll (tuple≠list) and **RLock between threads** freezing auto-refresh (only updated on click).
- ✅ **XP_POINTER found** (char struct offset `0x3C8`, int; current XP at level, resets on level-up; max not readable → % depends on XP-per-level table, friends building). Gold via `get_gold()` (0x410).
- ✅ **Delete REMOVED** from app (risk of accidentally deleting item): no tab, no checkbox, no execution. `DeleteConfig` stays dormant only for load compat.
- ✅ **UI:** sell tab reorganized (2 overlaps fixed), "Farm spot (map)" field + "Capture spot" button (client-side, no IPC), warning "keep dialogs left/visible", blue border on buttons, **"BotTO" desktop shortcut** (requests admin) + `start_botto.bat`.
- ✅ **Package for friends:** `BotTO_para_amigos.zip` (code + images/BMPs + install.bat + start_botto.bat + LEIAME). 0.5 MB, fits in Discord.

### 🔥 Done in session 2026-05-24 (part 2 — afternoon/evening) — commit `4dee204`
- ✅ **3 bugs reported by owner, fixed:**
  1. **Regen "sat and didn't resume attacking"** — only left rest with HP **and** MP at exactly 100%; if MP never filled (e.g., **Assassin has no mana**), froze sitting forever. Now leaves when recovering **above the threshold with margin** + **60s safety timeout**. New box **"Class without mana"** (`RegenConfig.ignore_mana`) in Regen tab ignores MP in rest. Farm radius ("Max distance from spot") now **40–100** (default 60).
  2. **Sell couldn't find "Sell Item" (friend's PC)** — fixed offset pointed to **1st row of menu** = "Purchase Item" at Blacksmith (opened wrong window → returned to spot). Now finds "Sell Item" by **IMAGE** (`sell_items_button.bmp`, threshold 0.85) + new **`window_to_client()`** converts capture coord (full window) → client area before clicking (fixes title bar Δ — the old thesis was right, the "resolution" guess was wrong). **Real sell validated live** (gold rose 435→448). ✅ task "real sell" complete.
  3. **Stop = EMERGENCY button** — `running` checks in sell loop (30 clicks) and map pathing; `trigger_sell_now` runs on **registered thread** that doesn't resurrect `running` after Stop; `stop_bot` **forces** stop and waits for main loop + manual sell.
- ✅ **Multi-account confirmed:** 2+ logged chars run in parallel (independent threads), each in the left list with its own dashboard. Fixed bug of **selection unchecking** (arrow from list cleared selection → now preserves by name).
- ✅ **Branding "Talisman Bot"** (pivot from "Automation SpAl"): owner's logo → `logo.png`/`logo.ico`, icon in window + taskbar + `.exe` build (nuitka). **DARK THEME** centralized in `UX/theme.py` (green/gold from logo), applied to all tabs. Logo banner at top of list. Start green / Stop red. "Talisman Bot" desktop shortcut.
- ✅ **UX:** **full tab scroll** (`ScrollableFrame`; flat combo, no own scroll); up-scroll bug fixed (only scrolls with overflow). **Fonts +2** across app. Fields **spread out** (HP/MP bands full-width, "Pot Key" at edge). **Autologin** reorganized (grid + button bar instead of fixed `place()`). Tooltip with **black font** (was white on light).

### 🔥 Done in session 2026-05-25 — Overnight farm OK + Drop detection via OCR
- ✅ **GATE MET: bot ran the WHOLE NIGHT (24→25/May) without freezing** — farm+sell cycle in production validated in practice. Unlocked next milestone (Sprint 4).
- ✅ **DROP DETECTION via System chat (Sprint 4, Phase 1) — DONE and live-validated.**
  - **Pivot pointer → OCR:** tried finding chat pointer via CE (level 6 scan, single base `client.exe+0x00C7C6CC`), but **dies on 2nd restart** — each chat line is reallocated heap (same problem as bag items). OCR is more robust and **doesn't break on TO update**.
  - **How it works:** finds chat by **ANCHOR** (3 chat icons template, `Images/misc/chat_anchor.bmp`, match 0.98) + calibrated region by relative offset to anchor; crops; preprocesses image (grayscale + 4x zoom + Otsu, `--psm 6`); OCR; extracts name from `You got the item: [Name(lvl X)]` by matching `[bracket]` (tolerant to OCR error; ignores "Congratulations" lines).
  - **Code:** `src/GhostBot/drop_watcher.py` (`DropWatcher.poll()` + helpers). Tools: `tools/test_ocr_chat.py` (tests treatments), `tools/calibrate_chat_region.py` (calibrates region live via mouse + anchor), `tools/test_drop_watch.py` (live loop).
  - **Lists:** `alertas_drop.txt` (root) — `[QUERO ALERTA]` (Medium/Large Ruby+Emerald) / `[NAO QUERO]` / outside both = "new item (decide)". Each player gets their own copy.
  - **60s live test:** detected `Animal Fur` as NEW, **dedup OK** (1 alert in ~35 reads), priming discards what's already on screen, didn't miss a drop.
  - **⚠️ `capture_window()` = CLIENT AREA** (not the full window); convert cursor with `ScreenToClient`, not `GetWindowRect` (the latter includes DWM's invisible border).
  - **Rarity by color:** the **item name comes in RARITY COLOR** (Animal Fur = WHITE name = common; the "You got the item:" prefix is fixed yellow). "White doesn't alert" filter is viable → **DEFERRED** (show only the name snippet via `image_to_data`; calibrate with more rarities; opaque chat background helps).
- ✅ **Phase 2 (Discord webhook) DONE:** `discord_notify.py` (urllib + `User-Agent` header to bypass Discord's HTTP 403). URL in `discord_webhook.txt` (gitignored, never commit). Live-validated (drops posted to channel). Want alert=🎯, new=❓, skip "don't want".
- ✅ **Phase 3 (integration into bot) DONE:** DropWatch + DeathAlert run on **PARALLEL THREAD** (`ThreadedBotController._run_monitor`, ~2s, independent of loop, respects Stop) — fixed the "sometimes detects, sometimes doesn't". Dashboard got: **"Session Drops" panel** (list + **x2 count**) + **✅ Want / ❌ Don't want** buttons (1-click triage → writes to `alertas_drop.txt`, becomes tag) + **CURRENT ACTION bar highlighted** (shows what bot does) + **DEATH alert** 💀 (HP=0 → Discord).
- ✅ **"Farm spot (map)" in Attack tab, synced with Sell** (1 capture = X,Y + map offset); offset moved to `AttackConfig` (saves even with Sell tab disabled).
- ✅ **Big batch of bot fixes (found testing):** Regen — recovers to ~95% (doesn't waste pot), max rest **16s**, resumes attacking immediately if aggressive mob, recovers BEFORE returning to spot, never rests/returns in combat. **RETURN to spot HYBRID** (near=minimap short steps / far=MAP open with decoy click), trigger = slider "Max distance from spot" (released **15-100**), + **"returning" mode** that persists until CENTERING (doesn't stop to fight on the way; anti-freeze after 6 cycles). Killed `_move_to_pos_via_map` (old upstream map-calculated that went to the wrong place). Drop count **x2** separate from Discord anti-spam.
- ⏭️ **NEXT:** **Boss target-lock** (front 4): flag + name box in Attack tab → TABs until name matches and attacks only it. Then: **pretty message** on Discord (embeds + rarity color + emojis), **rarity color filter** ("white doesn't alert"), and **embed Tesseract in the `.exe`** (no one installs anything). All committed LOCAL (no push yet).

### Next session starts with:
1. **XP-per-level table** (friends building) → connect **XP %** to dashboard
2. ✅ ~~Test real sell cycle~~ DONE. Remaining: run the **3-bag auto** cycle in real farm (1 bag validated).
3. **Validate Fairy team buff** + `TEAM_NAME` when team connects
4. ✅ ~~**Drop detection + Discord**~~ **COMPLETE** (Phases 1-3: OCR + webhook + parallel thread + dashboard with triage + death alert). Next big: **Boss target-lock** (front 4). Then: pretty Discord msg (embeds/rarity), rarity filter, Tesseract in `.exe`.
5. 🎯 **DECIDED: generate the .exe** (so friends don't need to install Python). Via GitHub Actions → **Build Executable** (run 2x: `client` and `server`). `minha-versao-estavel` branch already pushed to fork. Remaining: trigger the workflow, download the 2 .exe, test (watch for image path in binary — had bug before, see commits #30/#31). Since .exe are large, distribute via link (doesn't fit in Discord).

### How to run:
- **BotTO** desktop shortcut (auto-requests admin) or `start_botto.bat`.
- Config in `C:\\Users\\<user>\\GhostBot\\<charname>.yml` ($HOME, not LOCALAPPDATA — quirk).

---

## ✅ SPRINT 0 — Foundation (May 23 → Jun 03) — **100% complete** ("Inventory Full" via OCR DONE)

### Completed
- ✅ Python 3.11+ installed + `pip install .` of the fork
- ✅ Patches `game.exe → client.exe` (3 places: `client_launcher.py`, `threaded_bot_controller.py`, `lib/win32/process.py`)
- ✅ Admin permission for `pymem` (Claude Code + bot run as admin)
- ✅ Tesseract OCR installed (`pytesseract` binding not yet tested at runtime)
- ✅ First run `ghost-bot-server` + `ghost-bot-client`
- ✅ **Pointers validated at runtime:**
  - CHAR: name, level, HP, MAX_HP, MP, MAX_MANA, X, Y, location, gold, bag_1, bag_2
  - TARGET: select, ID, **HP (original chain works!)**, **name (POINTER_3)**
  - State: dialog, system_menu, notification, in_battle (reads but always returns 0 — broken)
- ✅ **CE session for TARGET_HP** — discovered that the chain `0x012CE2E0 + [0x18, 0x59C, 0x0, 0xC, 0x1F4, 0x15C, 0x480]` **already worked**. The `597` that looked like junk was **max HP on internal scale**; the calculation in `client_window.py` (`(value - 461) / (597 - 461) * 100`) normalizes to 0-100.
- ✅ **Bot ran and actually attacked** with `teste1231245` (Lv 2 in Green Scarp)
- ✅ Test char leveled from Lv 1 → Lv 2 during validation

### Sprint 0 Pending
- 🔄 OCR: **`pytesseract` validated at runtime + treatment tuned for chat** (drop detection, 2026-05-25). ✅ Mob/target name **resolved via POINTER** (`get_target_name`, used in Boss-lock + "Grab target" button). **Only "Inventory Full" remains.**
- ✅ ~~RaaskiBot v3.0 YouTube tutorials~~ — completed (feature references absorbed).
- ✅ ~~First real **Assassin** farm test from owner~~ — completed (real farm validated, not just test char).

---

## 🎨 UX REVOLUTION (extra, not in original plan)

Applied in this session on top of everything the bot already had:

### Reusable helpers in `src/GhostBot/UX/utils.py`
- **`Tooltip`** — yellow popup following cursor, font 11
- **`create_int_slider`** — min-max slider + editable entry + suffix. Supports `hint=` (tooltip) and `bg=` (line color)
- **`create_entry`** — text/boolean entry with label, supports `entry_width=`, `hint=`, `bg=`
- **`ComboWidget`** — dynamic combo (key+interval+remove lines) with internal scroll (~6 visible), `+ Add key` button. Flag `show_tab_button=False` hides TAB (used in Buff).
- **`NamedListWidget`** — listbox + add entry + `+`/`×` button. Used in item categories.
- **`setup_drag_from_listbox`** + **`widget_in_container`** — drag-and-drop from one listbox to another widget

### Redesigned tabs (all with PT-BR gamer + tooltips + left alignment)
- ✅ **Dashboard** (was Functions) — char info + target HP bar + "IN BATTLE" indicator + session stats (Mobs killed, Farm time). XP still placeholder.
- ✅ **Attack** — red HP band / blue MP band, % sliders, "No damage for (s)" slider, "Max distance from spot" with milestone tooltip, Combo dynamic (with "+ TAB" button to switch target), "Spot (X,Y)" with "Current Position" button
- ✅ **Regen** — same red/blue bands (but with threshold to sit out of combat). "Sit key" below.
- ✅ **Buff** — "Re-buff every" slider, dynamic Combo **without TAB** (buff doesn't switch target)
- ✅ **Fairy** — heal team + heal self (red bands), heal/cure/revive keys, spot. **NEW: Team Buff section** (combo + interval + "Buff self" checkbox). Logic in `fairy.py` (`_buff_team`, `_should_buff_team`) — validate when team connects.
- ✅ **Pet** — sliders for re-summon and feed (in minutes)
- ✅ **Sell** — existing config + **NEW: full-width bag item list + 3 categories (🗑️ Trash / 📦 Good / ✨ Super rare) + drag-and-drop** between bag → category
- ✅ **Delete** — only checkbox + interval slider

### Main window (`main.py`)
- 🎨 **DARK THEME** (2026-05-24, logo colors) centralized in `UX/theme.py`: bg `#14201C`, panels `#1B2B24`, green `#7CB518`/`#B4FB00`, gold `#FCB400`. (Was light blue `#4a90e2` before.)
- 📐 Responsive layout (grid + weights) — **resizable**
- 🪟 Tabs and log in `tk.PanedWindow` — **draggable divider**
- 🔘 Start button in "Accent" style (blue)
- 📏 Window 980×680 (min 820×560)

### Bug fixes
- 🐛 `bot_config.rege.hp_key` → `bot_config.regen.hp_key` (typo that made Save crash silently)
- 🐛 `_battle_pots` had HP/MP conditions swapped (checked `battle_hp_pot` but compared `battle_mana_threshold`)
- 🐛 Threshold sliders kept triggering (ui sent `60` but code expected `0.6`) — now `_as_decimal` auto-converts if value > 1
- 🐛 Dead code removed: `target_hp_full()` and `is_target_dead()` in `pointers.py`

### Bug fixes (2026-05-25 session — return to spot / regen / sell / drop)
- 🐛 **Regen "sat and didn't resume attacking"** — `_goto_start_location` required dist ≤ 2, but minimap click only PUSHES the char (no fine precision) → stayed in infinite nudge, never finished rest, never attacked. Fix: arrives with dist ≤ 8 + gives up if doesn't approach + attempt ceiling (commit `21c5090`).
- 🐛 **Return went to WRONG PLACE** (`move_to_pos` for dist > 50 fell to `_move_to_pos_via_map` — upstream map-calculated, which went to the wrong place). Fix: new `move_to_pos_minimap()` (minimap only, relative to char); map-calculated banned for in-zone movement (commit `5463278`).
- 🐛 **Runaway (char walked non-stop "to the left")** — clicking minimap EDGE = auto-walk continuous in TO + no timeout. Fix: clicked retreat INSIDE minimap (70% of reach, char goes and STOPS) + 5s timeout (commit `c8e9dbc`).
- 🐛 **Stopped to farm mid-return path** — mob on path cancelled the trip (anti-freeze gave up inside radius → farmed there). Fix: "returning" mode persists until CENTERING (doesn't attack while returning; anti-freeze after 6 cycles) (commit `7b7397c`).
- 🐛 **Post-sell freeze (up to ~60s stopped at spot without attacking)** — sell return required dist ≤ 3, impossible via map click. Fix: recognizes arrival when char STOPS walking (`block_while_moving`) (commit `0f186e2`).
- 🐛 **"Farm spot (map)" disappeared with Sell tab disabled** — field saved in Sell config; with Sell off Save discarded it (became None). Fix: field moved to `AttackConfig.return_spot_map_offset` (commit `5c77cac`).
- 🐛 **Drop "sometimes detects, sometimes doesn't"** — DropWatch read chat only BETWEEN loop actions; in heavy combat read rarely and drop disappeared. Fix: DropWatch + DeathAlert run on their own PARALLEL THREAD (~2s fixed) (commit `7ceb920`).
- 🐛 **Drop counted wrong (2 identical = 1)** — dedup for Discord also suppressed Dashboard count. Fix: `poll()` returns `(alerts, deltas)` — alerts with dedup (Discord doesn't spam), deltas count every new occurrence (commit `0bdc26a`).
- 🐛 **Regen wasted pot / sat too much** — left rest too early and re-sat. Fix: recovers to ~95% before returning (commit `f4a1340`) + max rest 16s and resumes attacking immediately if aggressive mob (commit `045ccbb`).
- 🐛 **Discord HTTP 403** — default urllib User-Agent blocked by Discord. Fix: `User-Agent: TalismanBot/1.0` header in `discord_notify.py`.

### Bug fixes (2026-05-26 session — `.exe` packaging for friends)
- 🐛 **Dashboard stuck on "loading." in the `.exe`** (combat worked, but no data on screen) — an **external submodule** (`GhostBot/lib/talisman_online_python` → `chestm007` repo) packaged an OLD version of `pointers.py` WITHOUT `get_xp` → `to_json` threw `AttributeError` every poll → UI never received data. Fix: submodule **REMOVED** (self-sufficient fork) + `submodules: recursive` removed from 3 workflows (commit `d625eed`).
- 🐛 **Discord didn't post + empty watchlist in `.exe`** — `discord_webhook.txt` and `alertas_drop.txt` weren't found (code didn't look in `.exe` folder, only in `~/GhostBot`, repo root and temp). Fix: candidates now include exe folder (`sys.argv[0]`), same as `_find_tesseract` (commit `8ba1d4a`).
- 🐛 **Tesseract didn't embed in `.exe`** — nuitka ignores `.dll`/`.exe` in `include-data-dir`. Fix: Tesseract goes as **folder next to** exe in package (`_find_tesseract` already looks there); validated.
- 🐛 **Server build #1 crashed** — `pytesseract` missing from `pyproject.toml` deps + `Images/` not embedded. Fix: commit `43e4afb`.
- ✨ **UI auto-recovers character list** — closing and reopening the UI no longer makes char disappear (asks for list every ~3s) (commit `cfd34e9`).

### Bug fixes (2026-05-26 session — part 2: Fairy "auto-select" + self-heal)
- 🐛 **Fairy auto-selected itself / healed ITSELF** (historic bug, multiple debugging sessions) — `get_with_case` (`lib/vk_codes.py`) added `+0x20` to UPPERCASE letters → the 'follow' key `P`(0x50) became **`0x70 = F1 = auto-select itself`**. Each P (follow) → self-selects → next `2` (heal) healed her. Fix: `return vk_codes[_key.lower()]` always (VK has no case; fixed ALL uppercase letters, e.g. 'A' became numpad). Live-validated. **NOT** phantom click / old code / stale `.exe` / TAB / autologin (all discarded along the way).
- 🧹 Removed debug instrumentation from `left_click` (`client_window.py`) that was leftover from diagnosis.
- ✨ **Fairy Helper: SELF-HEAL** (`fairy.py`, pending live test) — if HER HP < `heal_self_threshold` (default 50%): **F1 → heal → wait for cast → click 1st member → P**. + Helper now SELECTS the ally (backstage click on 1st member, `_select_ally`) each cycle — no longer depends on manual pre-selection.

### Bug fixes (2026-05-27 session — Fairy self-heal confirmed + client detection + friend bugs)
- ✅ **Fairy self-heal validated 100% live** — F1→heal→re-select 1st member→P flow works. Fairy front closed.
- 🐛 **Clients didn't appear in list if bot opened BEFORE them** (`controller/bot_controller.py:_scan_for_clients`) — the shortcut that skips scan compared only the PID set; a client opened on login screen (name=None) keeps the same PID after logging in → never re-evaluated → only appeared by restarting bot. Fix: only skip scan if nothing changed **AND** every running process already became a client in the list (`all_registered`). Live-validated; test `test_async_bot_controller` passes.
- ✅ **(friend) Shortcut didn't create — `DirectoryNotFoundException`** (`Criar atalho do Talisman Bot.bat`) — guessed `%USERPROFILE%\\Desktop`, nonexistent when OneDrive redirects Desktop. Fix: real Desktop via `[Environment]::GetFolderPath('Desktop')` + fallback. In both copies (repo + package).
- 🔴 **(friend) PENDING/PRIORITY — UI doesn't open (`run_client.exe`)** — only server opens; Defender blocks client (Nuitka false-positive). Resolve when owner asks; waiting for friend's diagnosis. See "RESUME HERE" block.
- 💊 **POTS: 16s cooldown (global — attack/boss/regen)** — pots in TO are regen over ~16s, not instant. Bot saw % still low right after potting and **potted again** (duplicate pot, "happened a lot"). Fix: 16s cooldown per pot key (`Runner._pot_ready`/`_use_pot`, `POT_DURATION_SECS=16`); recovery wait (`_wait_resource_refill`) now uses 16s. Applies to normal farm too, not just boss.

### New logic in `attack.py`
- ✨ **`_wait_resource_refill`** — after using HP/MP pot, bot **stops attacking** and waits for resource to fill (≥95%). By detection, not time. Leaves if HP drops again (under attack) or after 30s. Solves "attacking interrupts pot regen" problem.

---

## 🎯 PENDING TASKS — Cheat Engine session (consolidated)

| # | Task | Priority | What's needed |
|---|---|---|---|
| #3 | `TEAM_NAME_1` pointer | Low | Currently reads `'p2'` when alone. Validate when team connects before re-finding. |
| #4 | `BATTLE_STATUS` pointer | Low | Always reads 0. Not critical (combat detected indirectly by target HP dropping). Find for UI to show "IN BATTLE". |
| #5 | ~~`XP_POINTER`~~ ✅ **DONE** | — | Found 2026-05-24 at offset `0x3C8` of char struct (probes of ENERGY neighbors, no CE). Current XP at level (resets on level-up). Dashboard shows XP gained in POINTS. Only % remains (depends on XP-per-level table, friends building). |
| #6 | ~~Item name pointer in bag~~ ❌ **ABANDONED** | — | Pivot to template matching (BMPs in `Images/SELL`). Pointer scan level 4 doesn't survive restart in this game. DO NOT retry via CE. |

**Recommended strategy:** one CE session does all 4. Lessons learned from TARGET_HP session:
- Progressive scan (Unknown initial value → Decreased value → Unchanged value) works, but slow
- For values that change by "event" (battle status, XP), use 0→1 / N→N+X transition as filter
- The calculated address from the chain can be right BUT the final offset wrong — always read bytes around before discarding

---

## 🚧 NEW ITEMS DISCUSSED (not in original plan)

| Feature | Status | Notes |
|---|---|---|
| **Fairy Helper (heal + follow + SELF-HEAL, 1 member)** | ✅ DONE and 100% live-validated (2026-05-27) | Selects 1st member (backstage click) → heal → follow with P; self-heal (HP < 50%): F1→heal→back to 1st member. "Auto-select" bug (P→F1) RESOLVED. NO new UI (owner's decision). |
| **Party member selection (backstage)** | ✅ validated live | F1 = self; backstage click (`left_click`) = member. Coords `team_1..4` validated (1024x768, ~81px). ⚠️ DO NOT use real mouse. |
| **🐉 Cave Boss Bot (Boss tab, 3 roles)** | ✅ LIVE-VALIDATED (2026-05-27) — only DPS aggio pending | Dynamic tab (Tank/DPS/Fairy dropdown → fields change). TANK: boss-lock + combo + X buffs (no pots). DPS: boss-lock + retreat on aggro (lost HP→F1→wait→TAB) + recover MP. FAIRY: heal spam on current target. "Boss only Boss" rule. Spec in `CAVE_BOSS_BOT.md`. |
| **POTS with 16s cooldown** | ✅ DONE | Pot = ~16s regen; per-key cooldown prevents duplicate pot. In attack/boss/regen. |
| **⚔️ Attack: Class selector (DPS/Tamer/Fairy)** | ✅ DONE (2026-05-27), to validate | Dropdown at top of Attack tab. DPS=current. Tamer: pet attack key (when grabbing new target). Fairy: self-heal with skill instead of HP pot. Combo stays generic. |
| **🐾 Pet: Tamer + Normal (2 types, flags)** | ✅ LIVE-VALIDATED (2026-05-27) | `petfood.py` + Pet tab. **Tamer** (flag): summon/re-summon-on-death/feed. **Normal** (flag): only feed (own food). Fields appear by flag. Combat = Attack tab (combo). |
| **Fairy buff to GROUP (all members)** | reserved for a future routine | Buff entire group (F1 self + click each member). DIDN'T go into Cave Boss (tank/dps buff themselves; Cave Boss Fairy heals, doesn't group-buff). Separate from Helper. |
| **Dashboard with Kills + Time** | Working | Detects kill via target HP positive→dead transition |
| **Item categorization (Trash/Good/Rare)** | UI complete + drag-and-drop | Auto-sell/alert logic comes in Sprint 4. Needs task #6 (item names). |
| **Pause after pot for HP to fill** | Implemented in `attack.py` | By detection, not time |
| **Team set** (configure 4 friends' names for Fairy to buff) | Not started | Awaits team connecting to validate TEAM_NAME |
| **Standalone `.exe` package for friends** | ✅ DONE and live-validated | run_server + run_client + Tesseract (sibling folder) + 1-click launcher + icon; 139 MB zip on Drive. Self-sufficient fork (no external submodule). |
| **UI auto-recovers char list** | ✅ DONE | close/reopen without char disappearing (asks list every ~3s) — commit `cfd34e9` |
| **`gh` CLI (trigger/download builds)** | ✅ DONE | logged in as LpiresUrt; builds and .exe download from command line |

---

## 🎯 PRIORITY ORDER (updated 2026-05-26)

Reordered by owner. What to tackle, in order:
1. **Sprint 1 — FINALIZE** (in progress): friends testing `.exe` → 5 farming together + classes + mount + blacklist + Star Paths + Helper.
2. **Sprint 2 — Generic Cave Bot.**
3. **Sprint 7 — "Bots ready" (Scripts/Presets) + Robust save** ⬆️ (MOVED UP — in place of Security).
4. **Sprint 4 (rest)** — Auto-relog + Auto-Sell adjustments + rarity color filter + resilience.
5. **Sprint 5 — Buffer + Login + Interactive Discord Bot + v1.0 tag.**
6. **Sprint 3 — Security** ⬇️ (MOVED TO END — "not that important").

💡 **IDEAS (no timeline, won't do now):** mobile access via Tailscale (each uses their own PC), local HTML dashboard, and Sprint 6 (dedicated BC, Hollow Residuals, advanced anti-detection).

---

## 📅 SPRINT 1 — Multi-class + Loot + Logistics (Jun 04 → Jun 17)

**Status:** not started. Some related tasks already advanced via UX revolution.

- ⏳ 5-class configuration — **SIMPLIFIED (owner's insight 2026-05-26):** bot is key-based → combo is generic; each player configures their own keys and saves their own **SCRIPT** (Sprint 7). NO per-class code needed (Wizard/Monk/Assassin/Tamer). **Exception: Fairy** needs special logic — **Helper mode** ✅ **DONE** (selects 1st member via backstage click → heal → follow with P → re-buff; + **self-heal** via F1 when her HP drops < 50%). By key/click, no reading ally HP → works cross-PC. Old `_heal_team_member` logic (read HP from another bot on SAME machine) was replaced.
- 🔄 Installation on 4 friends' PCs — **IN PROGRESS:** standalone `.exe` package DONE AND LIVE-VALIDATED (`C:\\Bot\\Talisman Bot.zip`, 139 MB, zero installation). Only remaining: owner uploads to a link and friends run it.
- ⏳ Test: 5 farming simultaneously
- ⏳ Item Blacklist (Discovery Mode) — **UI partially ready** via Sell tab (Trash/Good/Rare). Remaining: "grab everything + drop log + UI checkbox" logic.
- ⏳ Mount system (mount/dismount + auto-mount on travel)
- ✅ Inventory Full detection via OCR — **DONE** (reads "Your item box is full." in same OCR as chat → 📦 Discord + auto-sell; timer = safety net)
- ⏳ Star Paths (Farm Spot ↔ City ↔ NPC) — structure exists in code
- ⏳ Petfood as independent module — **already exists in code**, UI done
- ✅ **Helper Mode v1 DONE** (heal + follow + self-heal 1st party member; all by key/backstage click). `P→F1` bug that froze everything (Fairy healed herself) was RESOLVED; Helper live-validated. Self-heal pending only live test.
- ⏳ Cheat Engine: boss pointers + item name on ground

---

## 📅 SPRINT 2 — Generic Cave Bot (Jun 18 → Jul 01) — **LARGE PART DONE via Cave Boss Bot**

The **Cave Boss Bot** (Boss tab) was built in 2026-05-27 and covers the heart of Sprint 2.
Live spec in `CAVE_BOSS_BOT.md`.

- ✅ **"Cave Mode" toggle separate from Farm** — became the **Boss tab** + "Boss" checkbox in Dashboard, with **"Boss only Boss"** rule (Boss on → unchecks/disables Attack/Sell/etc.).
- ✅ **"Role: Tank / DPS / Fairy" dropdown per char** — DONE (dynamic tab; fields change by role).
- ✅ **Boss Target Lock by configurable name** — DONE (commit `0f186e2`): "Lock onto Boss" + "Boss Name" in Attack tab (and reused in Boss); + **"🎯 Grab target" button** (`0d95dc7`). Tested live.
- ✅ **TANK / DPS / FAIRY specific logic** — ✅ LIVE-VALIDATED (2026-05-27), only DPS aggro pending:
  - TANK ✅: boss-lock + combo + buffs every Xs (auto-cast, no pot — Fairies heal).
  - DPS: boss-lock + recover MP ✅; **🔴 AGGRO CONTROL PENDING** (fine-tuning — HP threshold so it doesn't retreat from light AoE).
  - FAIRY ✅: heal spam on CURRENT TARGET (player switches target; doesn't read other HPs).
- ⏳ **3 rotations per char (Farm / Boss-DPS / Boss-Tank)** — partial: Farm (Attack tab) + Boss (Boss tab) ready; "saved rotations/preset" ties into Sprint 7.
- ⏳ **Real-time Debug panel / Auto-stop / Cave Stats** — not started.
- ⏭️ **Fairy GROUP buff (all members)** — base ready (`team_1..4`, `get_team_size`/`team_name_N`); DIDN'T go into Cave Boss (there Fairy heals, doesn't group-buff). Stays for a future routine if owner wants it.

---

## 📅 SPRINT 3 — Security — ⬇️ LOW PRIORITY, moved to END (owner's decision 2026-05-26: "not that important")

Original plan maintained. Not started.

- Auto-logoff at 20% HP
- Panic Stop (global F12)
- Varied delays between skills
- PvP detection (logoff if attacked)

---

## 📅 SPRINT 4 — Telemetry + Discord + Auto-Sell (Jul 16 → Jul 29)

**Status:** UI partially already done.

- ⏳ Session telemetry + history + per-role — **Dashboard already has kills + time**
- ⏳ Item Tier (5 levels) — **3 categories already exist in UI (Trash/Good/Rare), expand to 5 levels**
- ✅ Discord Webhook — **COMPLETE (2026-05-25 session):** drop detection via OCR + webhook (`discord_notify.py`) + parallel thread + dashboard (drops panel + triage ✅/❌ + action bar + death alert 💀) + **INVENTORY FULL alert 📦 (auto-sell)** + **EMBED alerts** (cards with color/char/time; color by type, ready for rarity). Remaining: **rarity color filter** (depends on rarity detection) and **close Tesseract in the `.exe`** — ZIP path ready (`tools/make_portable_tesseract.py` assembles portable `src/GhostBot/Tesseract-OCR/`, gitignored; code already finds it). CI (`build-executable.yml`) already embeds Tesseract+Images via `include-data-dir`; **standalone `.exe` DONE AND LIVE-VALIDATED (2026-05-26):** Tesseract goes as FOLDER next to exe (nuitka doesn't embed `.dll`/`.exe`), webhook/list found in exe folder, self-sufficient fork (submodule removed). Package `C:\\Bot\\Talisman Bot.zip` tested (dashboard + drop on Discord + death). **Only remaining:** rarity color filter.
- 💡 **[IDEA — won't do now]** Mobile access via Tailscale — each uses their own PC (owner's decision 2026-05-26).
- 💡 **[IDEA — won't do now]** Local HTML dashboard (5 chars in real-time).
- ✅ **Auto-Sell — DONE and running great** (sell cycle in production + auto-sell on inventory full). Only **FINE ADJUSTMENTS** remain if issues appear.
- ⏳ Resilience (retry + "just return" mode)
- 🔜 **Basic auto-relog — WE'LL DO** (in queue; owner's decision 2026-05-26).

---

## 📅 SPRINT 5 — Buffer + Login + Discord Bot (Jul 30 → Aug 12)

Original plan maintained. Not started.

- Bug fixes
- Account list (locally encrypted passwords)
- Interactive Discord Bot: `/status`, `/drops`, `/parar`, `/stats`
- Internal docs for friends
- v1.0 tag on fork

---

## 📅 SPRINT 6 — Post-Launch (optional)

- Dedicated BC (Farmer + Reseter + Shortcuts + Stats)
- Hollow Residuals (daily quest)
- Advanced anti-detection systems

---

## 📅 SPRINT 7 — "Bots ready" (Config Scripts/Presets) + Robust save — ⬆️ HIGH PRIORITY (moved up in place of Security; owner's decision 2026-05-26)

**Owner's request (2026-05-26):** be able to save a bot config as a reusable "script" ("simple bots ready") and switch between them with 1 click.

**Requirements:**
1. **"Save script" button:** saves CURRENT config (all tabs — Attack, Fairy, Boss, Pet, Sell) as a preset with NAME.
2. **Script list on the RIGHT SIDE:** mirrors the logged-in character list on the left. Each item shows **SCRIPT NAME** + **last update** in abbreviated format **`dd/mm/yy hh:mm`**.
3. **Apply by click:** clicking a script from the list **REPLACES** current config (loads preset into selected char's tabs).
4. ✅ **SUPER reliable save (DONE and LIVE-VALIDATED 2026-05-28):** Save no longer fails in **SILENCE**. `server.py` responds with `ERROR` and reason when `validate()` blocks; `main.py` shows it **VISIBLY** (green label "✓ Saved HH:MM:SS" / red popup + label on error). Never saves halfway (validation BEFORE saving; disk error also warns).

**Design notes (for when implementing):**
- Save scripts as named `.yml` files (e.g., `~/GhostBot/scripts/<name>.yml`), separate from per-character `<charname>.yml`.
- Timestamp = file `mtime` (or field saved in `.yml`), formatted `dd/mm/yy hh:mm`.
- "Replace current" = load preset into selected char's config + update UI tabs + save. Reuses load/save from `config.py`.
- Respect **Stop = emergency**: probably require bot **stopped** to switch scripts (don't switch config mid-farm).
- Save bug: see notes on silent save (memory `reference-save-must-succeed`).

---

## 🔒 SECURITY — Permanent Guidelines

- Talisman password different from email/other sites
- Game client only from official site
- Don't share login between friends
- Long daily breaks (4-8h off)
- Don't do top 1 ranking
- Bot **never** reads/writes password
- Private, closed group Discord
- Re-audit diffs before pulling upstream updates

---

## 🗂️ ARCHITECTURE — Quick Map

```
src/GhostBot/
├── run_server.py             # entry: ghost-bot-server (backend)
├── run_client.py             # entry: ghost-bot-client (tkinter UI)
├── controller/
│   └── bot_controller.py     # BotClientWindow: properties hp/mana/target_hp/etc.
│                             # to_json() sends everything to UI via IPC
├── functions/
│   ├── attack.py             # main combat loop + _battle_pots + _wait_resource_refill
│   ├── regen.py              # sit out of combat
│   ├── fairy.py              # heal team + buff team (NEW)
│   ├── buffs.py              # self-buff
│   ├── petfood.py            # Tamer pet
│   ├── sell.py               # path NPC + sell
│   └── delete.py             # delete junk
├── lib/talisman_online_python/
│   └── pointers.py           # ★ all memory pointers
├── UX/
│   ├── main.py               # main window + IPC UI client
│   ├── utils.py              # ★ reusable helpers (Tooltip, sliders, ComboWidget, NamedList, drag-and-drop)
│   └── tabbed_widget/
│       ├── functions.py      # Dashboard (renamed)
│       ├── attack_frame.py
│       ├── regen_frame.py
│       ├── buff_frame.py
│       ├── fairy_frame.py
│       ├── pet_frame.py
│       ├── sell_frame.py     # bag + 3 categories + drag-and-drop
│       └── delete_frame.py
└── config.py                 # dataclasses Config, AttackConfig, FairyConfig, SellConfig…
```

**Config persisted at:** `C:\\Users\\Owner\\GhostBot\\{charname}.yml` (HOME, not LOCALAPPDATA)
**Code reload:** server and client are separate processes. Change in `functions/*.py` → restart server. Change in `UX/*.py` → restart client.

---

## 🎬 NEXT SESSION — RESUME CHECKLIST

1. Read this `PROJECT_PLAN.md`
2. Confirm with owner: team connected? Assassin ready for real test?
3. If YES team connected → validate `team_name_X` and Fairy team buff
4. If YES Assassin ready → first real farm (not just test char)
5. CE session focused on 4 pending pointers (tasks #3, #4, #5, #6)
6. If all OK → start Sprint 1 (Loot Discovery + auto-mount)

---

## 📚 REFERENCES

- **Upstream:** https://github.com/chestm007/GhostBot
- **Memory pointers:** `src/GhostBot/lib/talisman_online_python/pointers.py`
- **Quick glossary:**
  - **Spot:** fixed X,Y point where bot stays
  - **Combo:** sequence of keys bot fires in loop
  - **Item tier:** classification Legendary > Super Rare > Rare > Uncommon > Common
  - **Cave Bot:** boss run mode (cave = cavern)
  - **Helper Mode:** 1 human char + 1 bot char helping
