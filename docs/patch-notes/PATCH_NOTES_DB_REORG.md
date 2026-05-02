---
type: patch-notes
version: meta
status: archived
systems:
  - architecture
  - obsidian
date: 2026-04-27
---

# Patch Notes — Database Reorganisation & Obsidian Brain Setup

**Date:** 2026-04-27
**Session Type:** Documentation restructure — no gameplay changes
**Files Modified:** All root-level .md files, README.md

---

## Summary

Full reorganisation of the project's documentation layer. All markdown files moved from the root into a structured `docs/` hierarchy. YAML frontmatter added to every document. Obsidian-native templates created. README rewritten for public GitHub presentation.

---

## Changes Made

### 1. New Folder Structure

Created `docs/` with four content subfolders and a templates folder:

```
docs/
├── play-tests/       ← 13 Play Test docs
├── patch-notes/      ← 17 Patch Note docs
├── handoff/          ← 6 Handoff docs
├── design/           ← 2 Design/Coding docs
└── _templates/       ← 4 Obsidian templates
```

### 2. YAML Frontmatter Added to All Docs

Every `.md` file now has an Obsidian-compatible frontmatter block:

```yaml
---
type: play-test | patch-notes | handoff | design | coding-doc
version: vX.X
status: archived | active | reference
systems:
  - combat
  - merchant
  - ...
---
```

**Tag taxonomy:**
- `type` — document category
- `version` — game version at time of writing
- `status` — `active` (current/in-use), `archived` (historical), `reference`
- `systems` — game systems the doc relates to: `combat`, `merchant`, `negotiate`, `stealth`, `character`, `world`, `ui`, `loot`, `items`, `architecture`

### 3. Four Obsidian Templates Created (`docs/_templates/`)

| Template | Use for |
|----------|---------|
| `Play Test Template.md` | New play test sessions |
| `Patch Notes Template.md` | Post-play-test fix passes |
| `Handoff Template.md` | Session handoff documents |
| `Coding Doc Template.md` | Feature specification docs for Claude |

### 4. README.md Rewritten

- Version corrected: v1.2 → v2.5
- Project structure tree updated with all current modules (`negotiate.py`, `pickpocket.py`, `merchant.py`, full `ui/` module)
- Negotiation system section added
- Roadmap updated to reflect completed and deferred features
- GitHub badges added (Python version, status, no dependencies)
- Minor polish: typography, prose tightening, emoji fix (Pokémon)

---

## Notes

- Original files remain in the root — not deleted. They can be removed once you've confirmed everything looks correct in Obsidian.
- Play Test 12 filename normalised: `Play test 12.md` → `Play Test 12.md` (capitalisation fix)
- `PT10_Handoff.docx` copied to `docs/handoff/` as-is (no frontmatter — binary file)
- Version tags on Play Tests 3, 4, 7, 8 are approximated from surrounding handoff docs — review and update in Obsidian if needed
