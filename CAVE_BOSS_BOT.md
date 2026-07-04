# 🐉 Cave Boss Bot — Context and Design

> Working document. We build **step by step**; each step is confirmed before coding.
> Created 2026-05-27 from owner's briefing.

## What it is

Mode for **CAVE BOSS** fights — different from normal spot farming. In boss fights nobody walks around: each person stays in their spot doing their role. Will become a **new "Boss" tab**
in the interface (separate from the others, for better organization).

**Default team (5):** 1 Tank + 2 DPS + 2 Fairies.

## The 3 roles

### 1. 🛡️ TANK (1)
- Hits **only the boss**, non-stop → uses **boss target-lock by name** (we already have: checkbox
  "Lock onto Boss" + name, TABs until found and attacks only it).
- Uses **some tank buffs**, like **every ~30s** (nothing major).
- **Base:** reuses Attack (with boss-lock on) + periodic buff. It's the simplest role.

### 2. ⚔️ DPS (2)
- Hits non-stop on the boss (also with boss-lock on the boss name).
- **Aggro control:** if a DPS **accidentally pulls aggro** → presses **F1 immediately** (deselects/stops hitting) + **waits for COMBAT to END** → tank repulls aggro by threat →
  DPS resumes hitting.
- **MP control:** if **MP drops** → same thing: **F1 → wait for combat to end → use pot**
  → resume hitting.
- It's the most **complex** role (needs to infer aggro — see "Limitations").

### 3. 🧚 FAIRY (2)
- **Heals whoever took damage** during the fight.
- Owner's initial plan: "**just spam heal and the player switches target**". So the
  simplest version = spam heal key on current target.
- ⚠️ **To define:** how does the Fairy choose WHO to heal (see "Limitations" — can't read other HPs
  from memory).

## ✅ What the bot CAN read/do (design foundation)

| Capability | How | Use in boss |
|---|---|---|
| Combat state | `client.in_battle` (✅ already used by Regen) | "wait for combat to end" (DPS) |
| Own HP/MP | `client.hp_percent`, `client.mana_percent` | pot trigger and "I'm getting hit" |
| Selected target | `get_target_name`, `target_hp`, `is_target_selected` | boss-lock (TAB until boss name) |
| Who's in party | `client.team_size`, `client.team_members` (names) | know how many/which members |
| Select member | backstage click `team_1..team_4` + `F1` (self) | switch heal target, DPS F1 |
| Press key | `client.press_key(...)` backstage | skills, pot, buffs |

## ⚠️ Limitations (important to know BEFORE promising)

- ❌ **Can't read OTHER members' HP** from memory — each bot only reads its **own** HP.
  → The Fairy **doesn't know on its own** "who is hurt".
- ❌ **Can't read who the boss is targeting** — no pointer for "enemy aggro".

### How to work around AGGRO (owner's question: "can we pull/read aggro?")
Reading boss aggro **directly: no.** BUT we can **INFER**: if a DPS is **getting hit**
(HP drops) while `in_battle`, it means the boss turned on them = pulled aggro.
→ DPS rule: "took damage in combat (not the tank)" → **F1 + wait `in_battle` to become false**
→ resume. Tank naturally repulls. Doesn't need to "pull aggro" actively — just **stop and wait**.

### How FAIRY chooses who to heal (pending decision)
Since it can't read other HPs, the options are:
- **(a)** Heal spam on **current target**; a human (or the flow itself) switches target. *(owner's initial plan — simplest)*
- **(b)** Fairy **cycles through portraits** (clicks member → heals → next → ...), healing everyone in rotation.
- **(c)** Another idea to discuss.

## 🧱 Construction plan (step by step — simplest to most complex)

1. ✅ **Boss tab** — DONE. **Role selector** (dropdown Tank/DPS/Fairy) + fields that **change
   by role** (owner's idea). Boss name + shared combo (Tank/DPS).
2. ✅ **TANK role** — DONE (2026-05-27, UI/UX validated by owner; logic = proven reuse
   of Attack). Locks onto boss (TAB until name) → attacks with combo → reapplies tank buffs every
   X s (just presses key, auto-cast, no target switch). HP/MP pots optional (empty key = off).
3. ✅ **FAIRY role** — DONE (2026-05-27). Option (a): spams heal key on CURRENT TARGET every
   `heal_interval_secs`; player switches target (clicks who needs it). No auto-aim (can't read
   other HPs). Own HP/MP pots optional. In tab, Fairy role hides Boss Name + Combo.
4. ✅ **DPS role** — DONE (2026-05-27). Hits boss (boss-lock + combo); **auto-aggro**:
   detects "pulled aggro" by **taking damage in combat** → F1 → waits for combat to end (`in_battle`
   → False) → tank repulls → resumes. **MP**: uses common MP Pot — when % triggers, F1 → waits for combat
   to end → pot → resumes. Reuses common fields (no new fields); aggro always on.

## ✅ ALL 3 ROLES READY (2026-05-27). Only need to validate DPS live + fine-tuning.

## 🔓 Decisions (resolved)
- ✅ **Architecture:** new runner (`functions/boss.py` + `BossConfig`), separate from farm.
- ✅ **Tank buff:** just presses the key (auto-cast, no F1). Buffs + interval = config in tab.
- ✅ **MP optional:** pot only fires with key filled; tank leaves MP empty.
- ✅ **Fairy:** option (a) — spam on current target, player switches.
- ✅ **DPS aggro:** trigger = **HP drop in combat** (`hp` dropped since last combo tick).
  No fine threshold for now (any drop retreats). Aggro **always on** (no toggle) — add
  on/off and/or threshold IF there's a false-positive in live test (e.g., light boss AoE).

## ⚠️ TO VALIDATE live (DPS) / possible adjustments
- **False-positive aggro:** if boss has AoE that takes a tiny bit from everyone, DPS might retreat for
  no reason. Easy fix if it happens: require drop > X% to count as aggro (becomes config).
- **"Combat end" time:** `_wait_out_of_combat` waits up to 20s. If tank takes long to repull,
  adjust timeout.
- **F1 = self:** confirm live that F1 really deselects boss target and stops damage (was the same
  F1 that Fairy uses to self-select — already validated there).

## ✅ "Boss only Boss" rule (ENFORCED in UI)
Checking the **"Boss"** checkbox in Dashboard **unchecks and disables** the others (Attack/Fairy/Buff/
Regen/Pet/Sell) — can't check the rest. Unchecking Boss re-enables. Guarantees boss mode
doesn't run together with normal farm (`FunctionsFrame._sync_boss_only`, trace in `bot_config.boss.enabled`).

## 🔁 DPS — re-grabs target (TAB) after F1
Both on aggro retreat and MP recovery, after **F1** + wait for combat to end
(+ pot, in MP case), DPS does **TAB** (`_find_boss`) to re-lock onto boss and resume hitting immediately.

## 💊 Pots: 16s cooldown (global) + Tank does NOT pot
- **Pots in TO are regen over ~16s** (not instant). Before, right after potting the % still
  looked low → bot potted again (duplicate pot, "happened a lot"). Fix: **16s cooldown
  per pot key** (`Runner._pot_ready`/`_use_pot`, `POT_DURATION_SECS=16`) — applied in
  **attack, boss and regen**. Recovery wait after potting also uses 16s (waits to "use the pot
  fully", leaving early if full).
- **Tank does NOT pot in boss** (owner's decision — Fairies heal tank): `_run_tank` doesn't call
  `_battle_pots`, and tab **hides pot fields when role is Tank**.
- DPS: HP Pot optional (cooldown) + MP recovery (retreat, pot, wait, TAB). Fairy: own pots
  optional (cooldown).
