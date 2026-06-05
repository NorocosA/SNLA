# AGENTS.md — StatsTalk

> Status: All phases complete. 110 tests (108 pass + 2 xfail). Production-ready.

## Architecture

```
User (自然语言)
  → LLM Planner (intent + method + variables)
  → Backend Router:
      ├─ Python (pingouin, 15 methods, SPSS optional)
      └─ SPSS (Python Submit / Batch)
  → Template Syntax (zero hallucination)
  → Validator (blacklist + greylist sandbox)
  → Executor → OMS XML / DataFrame Parser
  → Explainer (stat constraints → LLM polish)
  → User (白话解读 + Word export + MCP multi-channel)
```

**Dual backend**: SPSS for production, Python (pingouin) for no-SPSS mode. 11/12 methods cross-validated.
**RAG-enhanced**: SPSS documentation knowledge base (566 chunks) injected into LLM syntax fix + planner prompts.

## Commands

| Task | Command |
|------|---------|
| Setup | `python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt` |
| Dev run | `python launcher.py` (Flask + PyWebView window) |
| API only | `python snla/ui/server.py` (Flask on port 8501) |
| MCP server | `python snla/mcp_server.py` (stdio transport) |
| Tests (CI-safe) | `python -m pytest snla/tests/ -v -m "not slow"` (110 tests) |
| Single test file | `python -m pytest snla/tests/test_server.py -v` |
| Mock mode | `LLM_MOCK=true` in `.env` — no API key needed |
| Package | `pyinstaller snla.spec --noconfirm` → `dist/StatsTalk.exe` |
| Lint + format | `python -m ruff check snla/ && python -m ruff format snla/` |
| MCP integration | `python scripts/mcp_integration_test.py` |

## Environment

Copy `.env.example` → `.env`. Critical vars:

```
LLM_ENDPOINT=https://opencode.ai/zen/go/v1/chat/completions
LLM_API_KEY=your-key-here
LLM_MODEL=deepseek-v4-flash
STATS_BACKEND=spss          # "spss" | "python" | "auto"
SPSS_PATH=...               # Optional with Python backend
SPSS_PYTHON_PATH=...        # SPSS 26+ bundled Python
LLM_MOCK=true               # Dev without API key
SKIP_RAG=true               # Disable RAG knowledge base (optional)
```

## Test Strategy

- **110 tests** (108 pass + 2 xfail for pre-existing chi-square bug). No SPSS/LLM needed for CI.
- New test modules: `test_server.py` (23 Flask API tests), `test_python_backend.py` (24 pingouin tests)
- `conftest.py` fixtures: `sample_variables`, `mock_spss_output_ttest`, `analysis_result_ttest`, etc.
- `@pytest.mark.slow` on SPSS-dependent tests — deselect with `-m "not slow"`

## Server (`snla/ui/`) — design notes

**Module split** (Phase D): server.py (41KB → 3 files)
- `server.py` — Flask routes + global state only
- `_helpers.py` — `_make_executor`, `_has_llm`, `_load_dataframe`, `_check_rate_limit`
- `_pipeline.py` — `_run_python_backend`, `_prepare_syntax`, `_execute_and_parse`, `_syntax_template`, etc.

**Single-user design**: `_executing` bool blocks concurrent `/api/analyze` (returns 409).
**Rate limiting**: 60s window, 10 requests max for `/api/analyze`.
**Input sanitization**: 2000 char query limit, type validation.
**Session persistence**: SQLite shadow storage (`snla/data/persistence.py`) — survives restarts.
**Config hot-reload**: `/api/reload-config` POST endpoint.

### API endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Frontend HTML |
| GET | `/api/status` | Health + session state |
| POST | `/api/upload` | Upload .sav/.csv (500MB limit, MIME + extension check) |
| POST | `/api/analyze` | Main analysis pipeline |
| POST | `/api/cancel` | Cancel running analysis |
| POST | `/api/confirm` | Execute pending greylist operation |
| GET | `/api/variables` | Cloud-safe variable list |
| GET/POST | `/api/settings` | Read/update config |
| POST | `/api/reload-config` | Hot-reload .env |
| POST | `/api/models` | List available LLM models |
| GET | `/api/detect-spss` | Auto-detect SPSS installations |
| GET | `/api/export` | Download Word report |

## Constraints

1. **Windows-only** — SPSS automation requires SPSS bundled Python
2. **Syntax sandbox** — blocks SAVE, DELETE, HOST COMMAND, BEGIN PROGRAM, etc.
3. **Privacy** — only variable structure sent to LLM. `value_labels` stripped. Sensitive variable names detected and desensitized.
4. **TLS** — endpoint-specific permissive adapter for opencode.ai only. All other endpoints use default TLS.
5. **Upload limits** — 500MB max, `.sav`/`.csv` only, MIME validation.

## Module map

| Module | Purpose |
|--------|---------|
| `snla/config.py` | Env-var config, `validate()`, `reload_config()` |
| `snla/session.py` | In-memory `SessionState` (shadow-persisted to SQLite) |
| `snla/trust.py` | Trust whitelist (JSON runtime, compile-time fallback) |
| `snla/data/reader.py` | `.sav` → pyreadstat, `.csv` → pandas |
| `snla/data/sanitizer.py` | Cloud-safe filtering + sensitive var detection + desensitization |
| `snla/data/persistence.py` | SQLite session persistence (save/load/clear) |
| `snla/data/range_expander.py` | Q1-Q10 pattern detection + expansion |
| `snla/llm/client.py` | API wrapper, TLS adapter, exponential backoff retry |
| `snla/llm/prompts/` | intent.py, method.py, syntax.py — prompt templates |
| `snla/syntax/validator.py` | Blacklist, greylist, variable existence, bracket pairing |
| `snla/syntax/templates.py` | Pre-built SPSS syntax for 15 analysis types |
| `snla/executor/spss.py` | SPSS subprocess manager, OMS XML, temp copies |
| `snla/executor/python.py` | pingouin — 15 methods (12 core + Wilcoxon + multi/logistic regression) |
| `snla/executor/adapter.py` | BackendAdapter — unified SPSS/Python routing |
| `snla/orchestrator/` | Planner + greylist state machine (shared Flask/MCP) |
| `snla/orchestrator/planner.py` | LLM intent + method + variable matching, RAG-enhanced |
| `snla/mcp_server.py` | FastMCP 7 tools (stdio transport) |
| `snla/parser/_oms.py` | OMS XML parser — `parse_oms_xml`, 7 dedicated extractors |
| `snla/parser/_lst.py` | LST text parser — regex fallback |
| `snla/parser/output.py` | Unified `parse()` entry, re-exports |
| `snla/parser/schema.py` | `AnalysisResult`, `TableResult` dataclasses |
| `snla/explainer/naturalize.py` | Constraint layer + non-parametric templates (MWU, KWH) |
| `snla/explainer/export.py` | Word .docx export |
| `snla/explainer/charts.py` | matplotlib bar/scatter/histogram → base64 PNG |
| `snla/rag/` | RAG knowledge base (566 chunks, 20 commands) |
| `snla/ui/server.py` | Flask routes + global state |
| `snla/ui/_helpers.py` | Server helper functions |
| `snla/ui/_pipeline.py` | Analysis pipeline functions |
| `snla/ui/index.html` | Single-file frontend |
| `launcher.py` | Entry point: Flask thread → PyWebView window |

## File organization

```
snla/tests/              # 110 tests (10 files)
scripts/                 # Verification, demo, MCP integration test
data/fixtures/           # test_data.sav, airline.sav (25K), extended, boundary
docs/                    # user_guide, rename-evaluation, evaluation-and-testing-guide
.opencode/skills/snla/   # OpenClaw Skill config
pyproject.toml           # Ruff config (line-length=100, py310)
snla.spec                # PyInstaller → dist/StatsTalk.exe
```

## Current status

- [x] P0–P4: Complete (SPSS automation, Flask/PyWebView, packaging, E2E)
- [x] P5: Python backend (15 methods), BackendAdapter, trust whitelist
- [x] P6: MCP Server (7 tools), OpenClaw Skill, MCP integration test
- [x] P7: orchestrator/, Flask API tests (23), parser split, Ruff format, rename eval
- [x] P0/P1 Quality (8 grill fixes): parser tests, deps, upload limits, privacy, LLM retry, logging, analyze() refactor
- [x] Phase A-D (13 improvements): edge cases, input sanitization, rate limiting, session persistence, batch variables, non-parametric templates, Python backend tests, RAG pipeline, TLS hardening, config hot-reload, server split
- [x] Phase E: visualization (charts.py), extended stats (+3 methods), rename → **StatsTalk**

> Test count: **110** (108 pass + 2 xfail) | Python: 15 methods | MCP: 7 tools | API: 11 endpoints

## Known limitations

1. Single-user design — concurrent requests return 409
2. Windows-only — SPSS automation binds to Windows
3. Session in-memory with SQLite shadow — no multi-instance sync
4. `SPSSExecutor` type hint F821 — lazy import, harmless
5. `test_python_backend.py` 2 xfailed — pre-existing chi-square `expected.values()` bug
6. Batch variable analysis is pre-processor only — Q1-Q10 expanded before LLM, no multi-result aggregation yet
