# AGENTS.md — SPSS Natural Language Assistant (SNLA)

> Status: P4 测试与发布 (Testing & Release). 56 tests passing. See `Plan.md`.

## 🏗 Architecture
- **Core Loop**: User → LLM (Intent → Method → Syntax) → Validator → SPSS → Parser → LLM (Explanation) → User.
- **Backend**: Python 3.9+ (Windows only).
- **Frontend**: Flask REST API + HTML/CSS/JS, rendered via PyWebView native window (fallback: browser).
- **Packaging**: PyInstaller single-file .exe (`snla.spec`).

## 🚀 Key Commands
- **SPSS Execution**: Python Submit mode via SPSS bundled Python.
- **Setup**: `pip install -r requirements.txt`
- **Dev Run**: `python launcher.py`
- **API Only**: `python snla/ui/server.py`
- **Tests**: `python -m pytest snla/tests/ -v` (56 tests)
- **Package**: `pyinstaller snla.spec --noconfirm` → `dist/SNLA.exe`

## 🛡 Critical Constraints & Safety
1. **Windows-Only**: SPSS automation relies on SPSS bundled Python (`SPSS_PYTHON_PATH`).
2. **Syntax Sandbox**: Block any syntax modifying files on disk. 
   - **Forbidden**: `SAVE OUTFILE`, `DELETE`, `ERASE`, `DATASET CLOSE`, `NEW FILE`.
3. **Defensive Parsing**: SPSS output format varies by version/locale. Use regex + fixed-position extraction.

## 🔒 Privacy Protocol (MANDATORY)
- **Cloud LLMs**: ONLY send variable names, types, labels, and aggregate results (means, p-values).
- **NEVER** send raw data values or identifiers to cloud APIs.

## 📦 Implementation Guide
- **Metadata**: Use `pyreadstat` for `.sav` and `pandas` for `.csv`.
- **State**: In-memory session state (`snla/session.py`); no DB required.
- **API**: Flask server in `snla/ui/server.py`; frontend in `snla/ui/index.html`.
- **Patterns**: Modular (Intent → Method → Syntax → Validate → Execute → Parse → Explain).

## 🏁 Current Status
- [x] P0: Technical verification complete
- [x] P1: Core pipeline MVP complete
- [x] P2: Result explanation & safety complete
- [x] P3: UX optimization & reports complete
- [x] P4: Frontend migrated from Streamlit → Flask + PyWebView
- [ ] P4: Final packaging & release
