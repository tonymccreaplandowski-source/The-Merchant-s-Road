---
type: patch-notes
version: v2.0→v2.1
status: archived
systems:
  - character
  - merchant
  - ui
---

# Patch 11 — v2.0 → v2.1
**Date:** 2026-04-19
**Focus:** Context-Based Ambient Music

---

## Overview

The ambient music system now switches melody based on where the player is — road, city, dungeon, or tension. Previously a single loop played throughout the entire session with no regard for context.

---

## Four Ambient Contexts

| Context | Melody | Character |
|---|---|---|
| Road | A minor, haunting | Slow, sparse drone with descending phrases — existing track unchanged |
| City | C major, wandering | Bright and warm, a loose folk phrase with rise and fall |
| Dungeon | E minor, oppressive | Deep bass drone (E2), dissonant half-steps, long airless silences |
| Tension | A minor, urgent | Fast pulse, raised Bb3 injection, no settle — drives pressure |

All melodies loop continuously. The loop stops cleanly between context switches.

---

## Context Switch Points

| Trigger | Switches To |
|---|---|
| Game start | City (player begins in Rabenmark) |
| Travel begins (road_loop entry) | Road |
| City arrival (road_loop) | City |
| Enter cave or castle | Dungeon |
| Press deeper (mid-dungeon nav) | Tension |
| Retreat from location | Road |
| Flee from combat | Resumes previous context |
| Victory in combat | Resumes previous context |
| Fall back and escape dungeon | Road |
| All rooms cleared | Road |

Combat (flee or victory) now restores whatever context was playing before combat started, rather than always defaulting to road. This means dungeon combat correctly resumes dungeon music after the fight.

---

## Technical Notes

- `start_ambient_loop(context)` accepts `"road"`, `"city"`, `"dungeon"`, `"tension"`
- Same-context calls are no-ops (won't restart a running loop)
- Context switches join the old thread (0.6s timeout) before starting the new one
- `_current_context` global tracks the last active context
- `resume_ambient_loop()` restores `_current_context` — used at flee/victory call sites
- `display.py` now fully exports `show_combat_screen`, `show_character_sheet`, `show_journal` (file was previously truncated mid-function)
- `main()` entry point completed and version string updated to `v2.0 | Quality of Life Pass`

---

## Version String
`Alpha - World v2.0 | Quality of Life Pass` (set in this patch — was still showing v1.4)
