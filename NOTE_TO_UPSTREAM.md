# Hi chestm007 — notes on this GhostBot fork

Thanks a lot for GhostBot — it's been a great base to build on, and thanks for
reaching out on GitHub. Just to be upfront: **this is a small, non-commercial
hobby fork.** A few friends and I use it to farm together in Talisman Online.
I'm not trying to build anything fancy or sell anything — I just wanted a simple
farm bot to play with my group.

I don't really have a programming background, so I used an AI assistant to help
me adapt your code. Below is a short summary of what we changed, and then the one
thing I'm genuinely stuck on, in case you have a tip to share.

## What we built on top of your fork

(Windows-only. We tried Wine on Linux — the UI runs, but the server couldn't
find the TO clients.)

- **UI overhaul** — rebuilt the tkinter UI in Portuguese with a dark theme and a
  dashboard (HP/MP, current target, and session stats: kills, farm time, XP and
  gold gained).
- **Fixed-spot farming + sell cycle** — walk to the NPC, sell, return to the
  farm spot. Navigation is anchored to on-screen templates + offsets instead of
  hard-coded coordinates, so it survives window resize/move.
- **Fairy "helper" mode** — heals + follows an ally and self-heals, all through
  keypresses/clicks (it does **not** read another client's memory), so it works
  across separate PCs.
- **Cave Boss mode** — Tank / DPS / Fairy roles, with a boss target-lock by name.
- **Pet/Tamer support**, a per-class selector on the Attack tab, pot-cooldown
  handling, and a Discord webhook for drop + death alerts.
- **Save reliability fix** — saving config used to fail *silently* when
  validation rejected a field; now the server reports the reason and the UI
  shows it (green "saved" / red error popup).
- **Packaging** — standalone `.exe` via nuitka (GitHub Actions) so my friends
  don't need to install Python.

## Where I'm stuck — Cheat Engine, reading the Bag, and why we fell back to OCR

Character/target info works great through memory — HP, MP, position, level,
target name, gold, XP all read fine from pointers. The two things I could **not**
pin down via memory were:

1. **Bag / inventory item names.** I tried finding pointers with Cheat Engine,
   but the bag entries seem to be heap-allocated and the addresses don't survive
   a game restart (my pointer scans left no stable survivors). So for selling we
   ended up using template/image matching instead.

2. **Chat lines (drop detection / "inventory full").** Same problem — I found a
   chat base once, but each new chat line gets reallocated on the heap, so it
   broke on the second restart. We pivoted to **OCR** (anchor on the chat icons,
   crop the region, run Tesseract). It's surprisingly robust and survives game
   updates, but it's heavier than just reading memory.

**My question:** do you happen to know a reliable way to read the **bag
(item names/types)** or **chat text** from memory in TO? Even a hint about how
the inventory is laid out, or a pointer chain that survives restarts, would save
me a lot of OCR hassle.

## Things we drive with clicks/keys instead of memory

We never *write* to the game's memory — every action is a keypress or a
simulated click (via `SendMessage`, so it doesn't move the real mouse). We only
*read* memory for state. A few things we couldn't figure out how to do through
memory at all, so we do them with clicks on fixed screen positions, and I'd love
a better approach if you know one:

- **Selecting a party member** (for the Fairy's healing/follow logic). We click
  the party portraits at fixed coordinates (calibrated for 1024x768, ~81px
  spacing). I couldn't find any pointer to "select party member N", so this
  breaks if the resolution or UI layout changes.
- **Movement / returning to the farm spot** — we click the in-game map/minimap
  rather than driving the character through memory.
- **Selling at the NPC** — we click through the NPC dialog windows (anchored to
  on-screen templates).

If any of these (party selection especially) can be done from memory in TO,
that would be a huge help. No worries at all if you don't have the time —
anything you can share would be genuinely appreciated.

Thanks again for the project!

— LpiresUrt
