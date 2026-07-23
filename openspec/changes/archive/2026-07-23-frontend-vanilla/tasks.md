# Tasks: Frontend Vanilla — Zero-Build Clinical UI

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~260–310 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1: Foundation — Docker & Config

- [x] 1.1 Create `frontend/` directory under project root
- [x] 1.2 Verify `.dockerignore` does not exclude `frontend/`; add `!frontend/` if needed
- [x] 1.3 Add `COPY frontend/ frontend/` line to `Dockerfile` (after `COPY ranking/ ranking/`)

## Phase 2: Backend — StaticFiles Mount

- [x] 2.1 Modify `api.py` — replace `@app.get("/")` with `from fastapi.staticfiles import StaticFiles` + `app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")`

## Phase 3: Frontend — index.html Implementation

- [x] 3.1 Create `frontend/index.html` — HTML5 boilerplate, meta viewport, `<title>`, CDN scripts for `marked@18.0.6` and `dompurify@3.4.12`, link CSS design tokens
- [x] 3.2 Implement CSS: clinical design tokens (`--color-primary: #1a365d`, `--color-accent: #2b6cb0`, etc.), centered single-column layout (max-width 720px), form card, input + button styles, output area, spinner
- [x] 3.3 Implement JS: `DOMContentLoaded` → bind form submit → `showLoading()` (disable button, spinner with cold-start UX — first request "Iniciando motor clínico…", subsequent "Procesando consulta…") → `fetch("POST /consulta")`
- [x] 3.4 Implement JS: `handleSuccess(data)` pipeline — `urgencia`? render red banner → `motivo_parada === "confianza_insuficiente"`? render blue abstention notice → `marked.parse(respuesta)` → `DOMPurify.sanitize(html)` → DOM render → render `confianza` badge + hide loading
- [x] 3.5 Implement JS: `handleError(status)` — 422 shows "La consulta debe contener una pregunta." in error box, 503 shows "Servicio no disponible." in error box, input stays enabled for retry

## Phase 4: Testing & Verification

- [x] 4.1 Integration: start uvicorn, `curl http://localhost:8000/` — verify 200 + HTML content type
- [x] 4.2 Integration: `curl -X POST -H "Content-Type: application/json" -d '{"pregunta":"test"}' http://localhost:8000/consulta` — verify 200
- [x] 4.3 Manual: full UI flow — load browser, submit query, verify spinner → response → urgency banner → abstention notice → error states
