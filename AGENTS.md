# AGENTS.md — SPSS Natural Language Assistant (SNLA)

> Status: P0 技术验证 (Technical Verification). No code yet. See `Plan.md`.

## 🏗 Architecture
- **Core Loop**: User → LLM (Intent → Syntax) → Validator → SPSS (Batch/COM) → Parser → LLM (Explanation) → User.
- **Backend**: Python 3.9+ (Windows only).
- **Frontend**: MVP via Streamlit; Final via Electron/PyWebView.

## 🚀 Key Commands
- **SPSS Execution**: `& "C:\Path\To\spss.exe" -batch path\to\script.sps`
- **Setup**: `pip install pyreadstat pandas openai pywin32`

## 🛡 Critical Constraints & Safety
1. **Windows-Only**: SPSS automation relies on `spss.exe` or `win32com`. Do not attempt cross-platform SPSS logic.
2. **Syntax Sandbox**: Block any syntax modifying files on disk. 
   - **Forbidden**: `SAVE OUTFILE`, `DELETE`, `ERASE`, `DATASET CLOSE`, `NEW FILE`.
3. **Defensive Parsing**: SPSS output format varies by version/locale. Use regex + fixed-position extraction. Never assume English output.

## 🔒 Privacy Protocol (MANDATORY)
- **Cloud LLMs (OpenAI/Claude/DeepSeek)**: ONLY send variable names, types, labels, and aggregate results (means, p-values).
- **NEVER** send raw data values or identifiers to cloud APIs.
- **Local Models**: Use `llama.cpp` or `ollama` for full offline support if data sensitivity is high.

## 📦 Implementation Guide
- **Metadata**: Use `pyreadstat` for `.sav` and `pandas` for `.csv`.
- **State**: In-memory session state is sufficient for MVP; no DB required.
- **Patterns**: Follow a modular structure (Intent Recognition, Syntax Generation, Execution, Parsing).

## 🏁 Phase P0 Milestones
- [ ] Verify `spss.exe -batch` output redirection.
- [ ] Prototype "Syntax Generation" prompt efficiency.
- [ ] Basic "Echo" script: Text → Syntax → SPSS → Raw Output.
