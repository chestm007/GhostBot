# Note to upstream

Small hobby fork of GhostBot for Talisman Online farming with a few friends.

## What changed

- PT-BR UI overhaul with a dark theme and dashboard
- Fixed-spot farming, sell cycle, and return-to-spot navigation
- Fairy helper mode, cave boss mode, pet/tamer support
- Discord alerts for drops, inventory full, and death
- Safer save handling: the UI now reports validation/save errors instead of failing silently
- Standalone packaging via nuitka for friends who do not want to install Python

## Open issue

The two hard problems we still work around with OCR/template matching are:

- bag item names
- chat text / drop detection

If you know a stable memory path for either, that would save a lot of OCR hassle.
