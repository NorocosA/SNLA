# Project Rename Evaluation

## Current Name

- **Full:** SPSS Natural Language Assistant
- **Short:** SNLA
- **Package:** `snla`

## Why Consider Renaming

1. **SPSS is now optional.** The Python backend (pingouin) covers 11 of 12 analysis methods. SPSS is no longer required for most users.
2. **"SPSS" in the name misleads users** about dependency requirements. New users may think they need an SPSS license to use the tool.
3. **"Natural Language Assistant" is generic and verbose.** It describes the interaction style, not the core value (statistical analysis).
4. **"SNLA" is not memorable or searchable.** The acronym has no meaning outside the project, and search engines do not associate it with statistics or data analysis.

## Impact Analysis

| Layer | Scope | Items | Risk |
|-------|-------|-------|------|
| Python package | 190 imports | All `from snla.*` across the codebase | HIGH |
| PyInstaller | 1 file | `snla.spec`, output executable name | MEDIUM |
| UI / Frontend | 3 files | `index.html` title, sidebar header text | LOW |
| Documentation | 5+ files | README, AGENTS.md, Plan.md, user guide | LOW |
| MCP Server | 1 file | Server name and tool name prefixes (`snla_*`) | MEDIUM |
| Git repository | 1 | GitHub repository name and remote URL | LOW |

A full rename touches every layer. The Python package layer alone would require touching 190 import statements, plus PyInstaller paths, test fixtures, and CI scripts. That risk is not zero.

## Recommendation: Hybrid Approach

Keep the `snla` Python package name. Change only the user-facing branding.

This is the safest path. It avoids a brittle, wide-reaching refactor while still solving the core problem: the public name no longer matches the product reality.

### What changes

- **Display name:** "SPSS Natural Language Assistant" → candidate name (see below)
- **Short name:** "SNLA" → candidate short name
- **UI:** browser tab title, sidebar header, window title
- **README:** project title and description
- **MCP tools:** keep the `snla_` prefix. It is a stable API contract, and external clients already depend on it.
- **Launcher:** window title string

### What stays

- `snla/` package directory and all its contents
- All `from snla.xxx` imports inside `.py` files
- `snla.spec` PyInstaller configuration
- Environment variable names (e.g. `SPSS_PYTHON_PATH`)
- Internal module and class names

## Candidate Names

| Name | Short | Pros | Cons | Rating |
|------|-------|------|------|--------|
| **StatsTalk** | ST | Memorable, short, works in English and Chinese contexts, backend-agnostic | Somewhat generic | ★★★★ |
| **NaturalStats** | NS | Descriptive, clearly signals statistics | "Natural" is ambiguous (natural language? natural science?) | ★★★ |
| **DataSpeak** | DS | Easy to say, friendly | Less descriptive of the statistical focus | ★★★ |
| **SPSS Natural Language Assistant** | SNLA | Established, familiar to existing users | SPSS-dependent, long, increasingly inaccurate | ★★ |
| **StatWhisper** | SW | Catchy, distinctive | Too casual for academic or professional users | ★★ |

### Recommended: StatsTalk

- **Short:** 2 syllables, 8 characters. Easy to say and type.
- **Clear:** "Stats" signals the domain. "Talk" signals the natural language interface.
- **Bilingual-friendly:** Translates naturally into Chinese contexts without awkwardness.
- **Backend-agnostic:** Does not tie the product to SPSS, Python, or any future engine.

## Rename Cost (Hybrid Approach)

| Item | Effort |
|------|--------|
| UI changes (`index.html`) | 15 min |
| README + AGENTS.md updates | 15 min |
| Launcher window title | 5 min |
| **Total** | **~35 min** |

This estimate assumes no changes to the Python package, PyInstaller spec, or MCP tool names. A full rename (including the package) would take 4 to 8 hours and introduce regression risk across 190 imports.

## Decision

This document presents the tradeoffs. The final choice is yours.

- [ ] **Keep "SPSS Natural Language Assistant (SNLA)"** — postpone rename, accept the branding mismatch
- [ ] **Adopt "StatsTalk"** — implement hybrid rename (keep `snla` package, update user-facing text only)
- [ ] **Other:** ____________

If you select "StatsTalk" or another candidate, the next step is a single 35-minute pass through the UI, README, and launcher files. No code logic changes required.
