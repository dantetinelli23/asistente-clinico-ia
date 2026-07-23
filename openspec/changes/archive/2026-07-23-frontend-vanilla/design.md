# Design: Frontend Vanilla — Zero-Build Clinical UI

## Technical Approach

Single-file `frontend/index.html` served via FastAPI `StaticFiles` at GET `/`. Vanilla JS calls `POST /consulta` via `fetch()`, pipes `respuesta` through marked.js → DOMPurify → DOM. No bundler, no framework, no npm. CDN libs pinned in `<script>` tags.

## Architecture Decisions

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Single `index.html` vs split CSS/JS | Single = 1 HTTP request, simpler deploy, bigger file; Split = separation, cacheable, 3 requests | **Single file** — simpler, matches proposal intent, HTTP/2 at Cloud Run makes multiple requests cheap but single is still simpler |
| Mount StaticFiles at `/` vs subpath | Subpath avoids route conflict but changes URL | **Mount at `/`** — remove existing `@app.get("/")`; `html=True` serves index.html automatically; POST `/consulta` stays because FastAPI routes take precedence over mounts |
| Inline CDN via `<script>` vs downloaded + served locally | Download = CDN reliability risk, no offline; Local = Docker image size + CORS-free | **CDN `<script>` tags** — zero build, cacheable by browser, smaller container, cdnjs/esm.sh reliability is fine for production |
| marked.js 18.0.6 vs older | 18.x is latest stable, no known regressions, good browser compat | **18.0.6** via esm.sh or cdnjs |
| DOMPurify 3.4.12 vs older | 3.4.12 is latest with zero CVEs | **3.4.12** — latest secure version |

## Data Flow

```
Browser                    FastAPI                   LangGraph
  │                          │                          │
  ├── GET / ───────────────► │                          │
  │ ◄── index.html ───────── │                          │
  │                          │                          │
  ├── POST /consulta ──────► │                          │
  │   {pregunta: "..."}      ├── grafo.ainvoke() ──────►│
  │                          │◄── resultado ────────────│
  │ ◄── {respuesta,          │                          │
  │       confianza,         │                          │
  │       urgencia, ...}     │                          │
  │                          │                          │
  │  [marked.parse()]        │                          │
  │  [DOMPurify.sanitize()]  │                          │
  │  [DOM render]            │                          │
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/index.html` | Create | Single-file vanilla HTML+CSS+JS clinical UI |
| `api.py` | Modify | Replace `@app.get("/")` with `StaticFiles` mount at `/` |
| `Dockerfile` | Modify | Add `COPY frontend/ frontend/` line |
| `.dockerignore` | Modify | Ensure `frontend/` is NOT ignored (currently only excludes `venv/`, `__pycache__/`, etc.) |

## Interfaces / Contracts

**CDN Dependencies (pinned in `<script>` tags):**

```html
<script src="https://cdn.jsdelivr.net/npm/marked@18.0.6/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.4.12/dist/purify.min.js"></script>
```

**API contract consumed by JS:**

```
POST /consulta → 200: { consulta_id, respuesta (markdown string), confianza (float|null), urgencia (bool), motivo_parada (string|null) }
POST /consulta → 422: { detail: "La consulta debe contener una pregunta." }
POST /consulta → 503: { detail: "El servicio no pudo procesar la consulta..." }
```

**Markdown rendering pipeline:**

```
respuesta (raw markdown)
  → marked.parse(respuesta) → HTML string
  → DOMPurify.sanitize(html) → safe HTML
  → element.innerHTML = safeHtml
```

## CSS Architecture

| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary` | `#1a365d` | Header, primary text |
| `--color-accent` | `#2b6cb0` | Button, links, focus ring |
| `--color-bg` | `#f7fafc` | Page background |
| `--color-surface` | `#ffffff` | Card background |
| `--color-border` | `#e2e8f0` | Card borders, dividers |
| `--color-error` | `#fc8181` | Error box background |
| `--color-urgency` | `#fed7d7` | Urgency banner background |
| `--color-abstention` | `#bee3f8` | Abstention notice background |
| `--color-confidence` | `#38a169` | Confidence badge (high) |
| `--color-muted` | `#718096` | Secondary text |

Layout: centered single-column, max-width 720px, stacked cards. No sidebar, no chatbot bubbles, no avatars.

## JS Architecture

```
DOMContentLoaded
  └─► bind form submit
        └─► showLoading()   // disable button, show spinner
              └─► fetch("/consulta", { method: "POST", body: JSON })
                    └─► response.ok?
                      ├─ YES → handleSuccess(data)
                      │        ├─ urgencia? → renderUrgencyBanner()
                      │        ├─ motivo_parada? → renderAbstention()
                      │        ├─ renderRespuesta(marked.parse(respuesta))
                      │        ├─ renderConfianzaBadge()
                      │        └─ hideLoading()
                      └─ NO  → handleError(status)
                               ├─ 422 → showError("La consulta debe contener una pregunta.")
                               ├─ 503 → showError("Servicio no disponible.")
                               └─ hideLoading()
```

Cold-start UX: `let isFirstRequest = true` — first POST shows "Iniciando motor clínico…", subsequent show "Procesando consulta…".

## Testing Strategy

| Layer | What | How |
|-------|------|-----|
| Integration | StaticFiles mount serves index.html | Start uvicorn, `curl http://localhost:8000/` — verify 200 + HTML |
| Integration | POST /consulta still works | `curl -X POST -H "Content-Type: application/json" -d '{"pregunta":"test"}' http://localhost:8000/consulta` |
| Manual | Full UI flow | Browser at localhost:8000, submit query, verify spinner → response → rendering |
| Manual | Error states | Stop backend → submit → verify 503 error box renders |
| Manual | Urgency/abstention | Needs test data that triggers `motivo_parada` or `es_urgencia` |

## Migration / Rollout

No migration. Remove existing `@app.get("/")`, add `StaticFiles` mount, rebuild Docker image, redeploy to Cloud Run. Rollback: revert `api.py`, remove `frontend/`, rebuild.

## Open Questions

- [ ] Should we add a favicon or is the browser default fine for now?
