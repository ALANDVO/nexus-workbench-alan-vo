# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

decompiler-analysis

## Roadmap

### core-skeleton — FastAPI/React skeleton with auth and domain engine

Status: done

Acceptance:
- FastAPI app starts and serves health endpoint
- React frontend builds and loads
- OIDC Keycloak auth flow configured
- SQLite persistence with migrations
- Docker compose runs backend, frontend, Keycloak
- CI workflow runs backend/frontend tests

Implementation: `backend/app/main.py`, `backend/app/api/auth.py`, `backend/app/api/analyses.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/auth.py`, `backend/app/models/user.py`, `backend/app/models/analysis.py`, `backend/tests/test_health.py`, `backend/tests/test_auth.py`, `backend/tests/test_analyses.py`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/hooks/useAuth.tsx`, `frontend/src/api/client.ts`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/pages/CallbackPage.tsx`, `frontend/src/pages/DashboardPage.tsx`, `frontend/src/pages/AnalysisListPage.tsx`, `frontend/src/pages/AnalysisDetailPage.tsx`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/components/Layout.tsx`, `frontend/tests/useAuth.test.tsx`, `frontend/tests/client.test.ts`, `compose.yaml`, `.github/workflows/ci.yml`

Tests: `backend/tests/test_health.py`, `backend/tests/test_auth.py`, `backend/tests/test_analyses.py`, `frontend/src/hooks/useAuth.test.tsx`, `frontend/src/api/client.test.ts`

### decompiler-analysis — Decompiler output analysis engine

Status: done

Acceptance:
- Parse decompiler output into structured AST
- Identify indirect calls (vtable, switch, JMP/PUSH patterns)
- Resolve function targets from cross-references

Implementation: `backend/app/services/decompiler_engine.py`, `backend/app/services/analysis_service.py`, `backend/app/api/analyses.py`, `frontend/src/types/index.ts`, `frontend/src/api/client.ts`, `frontend/src/pages/AnalysisDetailPage.tsx`

Tests: `backend/tests/test_decompiler_engine.py`, `backend/tests/test_analysis_service.py`

### vtable-resolution — VTable function call resolver (Issue #516)

Status: done

Acceptance:
- Detect vtable patterns in decompiler output
- Resolve indirect calls to concrete function names
- Display resolved calls in UI with navigation

Implementation: `backend/app/services/decompiler_engine.py`

Tests: `backend/tests/test_decompiler_engine.py::TestDecompilerEngine::test_detect_vtables`, `backend/tests/test_decompiler_engine.py::TestDecompilerEngine::test_resolve_vtable_calls`

### switch-recovery — Switch statement recovery (Issue #2628)

Status: done

Acceptance:
- Recognize jump-table switch patterns
- Reconstruct switch cases from comparison chains
- Render as switch in decompiler view

Implementation: `backend/app/services/decompiler_engine.py`

Tests: `backend/tests/test_decompiler_engine.py::TestDecompilerEngine::test_recover_switches`

### jmp-call-recovery — JMP-with-PUSH call recovery (Issue #5747)

Status: done

Acceptance:
- Detect PUSH+JMP call patterns
- Recover return addresses for correct CFG
- Render as proper call sites in decompiler

Implementation: `backend/app/services/decompiler_engine.py`

Tests: `backend/tests/test_decompiler_engine.py::TestDecompilerEngine::test_detect_jmp_push_calls`

### string-recovery — Cross-segment string recovery (Issue #4865)

Status: done

Acceptance:
- Scan all memory segments for string data
- Associate string references in decompiler
- Display strings inline in decompiler view

Implementation: `backend/app/services/decompiler_engine.py`

Tests: `backend/tests/test_decompiler_engine.py::TestDecompilerEngine::test_extract_strings`

### batch-decompiler — Scalable batch decompilation (Issue #2791)

Status: planned

Acceptance:
- Parallel decompilation with work-stealing queue
- Shared analysis cache across workers
- Benchmark shows linear scaling to 16+ cores

