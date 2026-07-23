# Proposal: Frontend Vanilla

## Intent

Single-page frontend served by FastAPI (no build step) so clinicians can submit queries and see structured responses. Today there's no human interface — only POST /consulta. This unlocks real-time clinical decision support without requiring curl/Postman.

## Scope

### In Scope
- Static HTML+CSS+JS served via FastAPI on GET /
- Text input + submit button with loading indicator (cold-start UX)
- Markdown render of **bold** and numbered lists in `respuesta`
- Urgency alert banner when `urgencia=true` (prominent, distinct)
- `confianza_insuficiente` abstention shown as informative notice, not error
- 422/503 error display (distinct from abstention)
- Professional clinical UI: sober palette, no chatbot aesthetics
- Safe HTML rendering of `respuesta` (sanitized)

### Out of Scope
- Conversation history, login, multi-turn, build step, npm, testing

## Capabilities

### New Capabilities
- `frontend-web`: Zero-build vanilla web UI for clinical queries

### Modified Capabilities
- None

## Approach

Mount `frontend/` as `StaticFiles` at GET / in `api.py`. Single `index.html` with inline CSS/JS calls `POST /consulta` via `fetch()` and renders each response field into targeted DOM elements. Use lightweight CDN libs for markdown parsing and HTML sanitization (marked.js + DOMPurify or client-side equivalent). No bundler, no framework — pure ES modules or script tags.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `api.py` | Modified | Add `StaticFiles` mount for GET / → `frontend/` |
| `frontend/index.html` | New | SPA page (HTML + embedded CSS/JS) |
| `Dockerfile` | Modified | Copy `frontend/` into container image |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Cloud Run cold start delays first response | High | Loading spinner + "warming up" message |
| HTML in `respuesta` is XSS vector | Medium | Sanitize via DOMPurify before rendering |

## Rollback Plan

Remove `StaticFiles` mount from `api.py`. GET / reverts to `{"estado": "vivo"}`. No data migration — frontend is stateless.

## Dependencies

- None (CDN: marked.js, DOMPurify — pinned in design)

## Success Criteria

- [ ] GET / serves a functional HTML page
- [ ] Input + button submits to POST /consulta and renders response
- [ ] Loading state visible during request
- [ ] **bold** and numbered lists render correctly
- [ ] Urgency banner visible when `urgencia=true`
- [ ] `confianza_insuficiente` shows as notice, not error
- [ ] 422/503 shows distinct error message
- [ ] Sober clinical design, no chatbot colors
