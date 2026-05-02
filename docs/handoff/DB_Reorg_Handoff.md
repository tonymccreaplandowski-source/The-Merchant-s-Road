---
type: handoff
version: meta
status: archived
systems:
  - architecture
  - obsidian
date: 2026-04-27
---

# Handoff — Database Reorganisation & Obsidian Brain Setup

**Date:** 2026-04-27
**Session Type:** Documentation restructure — no gameplay changes
**Working folder:** `C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\`

---

## Git Push Workflow

ALWAYS follow this order — the working folder is in OneDrive and is NOT the git repo:

```bat
xcopy /E /Y "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\*" "C:\dev\merchants-road\game\"
cd C:\dev\merchants-road
git add -A
git commit -m "message"
git push
```

**Optional — if you want docs on GitHub too:**
```bat
xcopy /E /Y "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\docs\*" "C:\dev\merchants-road\docs\"
```

---

## What Was Done This Session

Full reorganisation of the documentation layer. No game code was modified.

### 1. New Folder Structure

All `.md` files moved from the root into `docs/` with clean subfolders:

```
docs/
├── play-tests/       ← 13 Play Test docs
├── patch-notes/      ← 17 Patch Note docs (including PATCH_NOTES_PT10 and DB_REORG)
├── handoff/          ← 6 Handoff docs
├── design/           ← Expansions.md, Pickpocket_Coding_Doc.md
└── _templates/       ← 4 Obsidian templates
```

### 2. YAML Frontmatter

Every `.md` file has an Obsidian-compatible frontmatter block with four fields: `type`, `version`, `status`, `systems`. Obsidian's Properties panel will surface these immediately.

**Tag taxonomy:**
- `type`: `play-test` | `patch-notes` | `handoff` | `design` | `coding-doc`
- `version`: game version at time of writing (e.g. `v2.5`)
- `status`: `active` | `archived` | `reference`
- `systems`: `combat`, `merchant`, `negotiate`, `stealth`, `character`, `world`, `ui`, `loot`, `items`, `architecture`

### 3. Templates (`docs/_templates/`)

| Template | Use for |
|----------|---------|
| `Play Test Template.md` | New play test sessions |
| `Patch Notes Template.md` | Post-play-test fix passes |
| `Handoff Template.md` | Session handoff documents |
| `Coding Doc Template.md` | Feature specs for Claude |

To use in Obsidian: Settings → Templates → set template folder to `docs/_templates`.

### 4. README

Updated from v1.2 to v2.5. Full module tree documented. Negotiation section added. Roadmap refreshed. GitHub badges added.

---

## State of the Root

Root now contains only:
- `README.md`
- `game/` (unchanged)
- `docs/` (new)
- `.gitignore`

All original root-level `.md` files deleted after confirming copies exist in `docs/`.

---

## One Thing to Watch

Version tags on **Play Tests 3, 4, 7, and 8** are approximated — solid anchors existed for PT5 (v2.0), PT6 (v2.2), PT10 (v2.6), and PT13 (v2.7), but the middle ones were estimated. Worth a quick review in Obsidian's Properties panel if precision matters.

---

## Next Session

No outstanding items from this session. Resume from Play Test 13 / Pickpocket coding doc (`docs/design/Pickpocket_Coding_Doc.md`) — target version v2.7 → v2.8.
