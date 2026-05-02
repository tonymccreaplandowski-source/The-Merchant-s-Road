---
type: patch-notes
version: v2.2-hotfix
status: archived
systems:
  - combat
  - ui
---

# Patch 12.1 — v2.2 Hotfix
**Date:** 2026-04-20
**Session:** Post-session repair (carry-forward damage from Patch 12 cat >> appends)

---

## What Was Broken

Three files were left in a broken state at the end of the Patch 12 session due to file truncation and bash append side-effects.

### `main.py` — IndentationError on launch
- The `cat >>` append that restored `road_loop`, `game_over`, and `main()` after the original truncation left orphaned hermit/shady_figure code fragments *after* the `if __name__ == "__main__": main()` line
- Python raised `IndentationError: unexpected indent` at the first orphaned print statement (line 2532 at time of error)
- Additionally, `main()` itself was not present in the file — it had been dropped during an earlier repair pass
- **Fix:** Truncated to the last clean line (`sys.exit(0)` in `game_over`), then appended a clean `main()` and `if __name__` block

### `enemies.py` — Null bytes + duplicate function
- File contained 89 trailing null bytes from a prior bash write operation
- Also had a duplicate `def spawn_enemy` definition (the first a stub, the second complete) — Python used the second (correct) one, but it was messy
- **Fix:** Stripped null bytes; removed duplicate stub definition via Edit

### Syntax audit
All six game files now pass `ast.parse()` with no errors:
- `data/enemies.py` ✓
- `data/items.py` ✓
- `engine/player.py` ✓
- `engine/combat.py` ✓
- `ui/display.py` ✓
- `main.py` ✓

---

## Notes for Future Sessions

- Prefer `Edit` over `Write` or `cat >>` for all file modifications — large writes and bash appends are the root cause of all truncation/corruption issues in this project
- After any repair involving `cat >>`, immediately run the syntax audit script to catch orphaned fragments before they reach play test
- The audit script is at: `C:\Users\user\AppData\Roaming\Claude\...\outputs\deep_audit.py`
- If the title screen does not read `Alpha - World v2.2`, you are running a stale copy of the game

---

## Files Modified

| File | Change |
|---|---|
| `main.py` | Restored `main()` and `if __name__` entry point; removed orphaned event fragments |
| `data/enemies.py` | Stripped 89 trailing null bytes; removed duplicate `spawn_enemy` stub |
