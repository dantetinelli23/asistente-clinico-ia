# Frontend Web Specification

## Purpose

Zero-build vanilla web UI for clinical decision support. Served via FastAPI static mount — no bundler, no npm, no framework.

## API Contract

### POST /consulta

**Request:** `{ "pregunta": "string — consulta del profesional" }`

**Response 200:**
```json
{
  "consulta_id": "uuid",
  "respuesta": "string — markdown con **bold** y listas",
  "confianza": "float | null — puntaje 0-1 del juez",
  "urgencia": "boolean — true = escalar a humano",
  "motivo_parada": "string — confianza_insuficiente | urgencia:* | etc."
}
```

## Error Handling Matrix

| Condición | HTTP | Display |
|-----------|------|---------|
| Validación fallida | 422 | Error: "La consulta debe contener una pregunta." |
| Servicio no disponible | 503 | Error: "El servicio no pudo procesar la consulta." |
| Confianza insuficiente | 200 | Notice informativo (NO error) |
| Urgencia detectada | 200 | Banner prominente + respuesta normal |
| Consulta exitosa | 200 | Respuesta + badge de confianza |

## Requirements

### FR-1: Static Serving
GET / MUST serve index.html via FastAPI `StaticFiles`.

#### Scenario: Page loads
- GIVEN a browser at GET /
- WHEN the page loads
- THEN an input field and submit button are visible

### FR-2: Query Submission
The form MUST POST `{"pregunta": "<input>"}` to /consulta via `fetch()`.

#### Scenario: Happy path
- GIVEN the user types "¿Dosis de ibuprofeno en niños?"
- WHEN they click Enviar
- THEN POST /consulta is called with the pregunta
- AND a loading spinner appears

### FR-3: Response Rendering
Each response field MUST render into a targeted DOM element.

#### Scenario: Render all fields
- GIVEN API returns 200 with consulta_id, respuesta, confianza, urgencia
- WHEN the response is received
- THEN respuesta renders in the output area
- AND confianza shows as a badge
- AND consulta_id is hidden metadata

### FR-4: Loading State
A loading indicator MUST appear on submit and MUST be removed on response.

#### Scenario: Cold start delay
- GIVEN the user submits a query
- WHEN Cloud Run cold start delays > 2s
- THEN a spinner with "Iniciando motor clínico…" is visible
- AND the submit button is disabled

### FR-5: Markdown Rendering
The system MUST parse and render **bold** and numbered lists from respuesta using marked.js.

#### Scenario: Bold + numbered list
- GIVEN respuesta contains `**importante**` and `1. Paso uno\n2. Paso dos`
- WHEN rendered
- THEN bold text uses `<strong>` and list uses `<ol><li>`

### FR-6: Urgency Banner
When `urgencia` is true, the system MUST show a prominent banner above the respuesta.

#### Scenario: Urgency flagged
- GIVEN API returns `urgencia: true`
- WHEN response renders
- THEN a red/orange banner with "⚠ URGENCIA — Se requiere evaluación médica inmediata" appears

### FR-7: Abstention Notice
When `motivo_parada` is `confianza_insuficiente`, the abstention MUST display as an informative notice, not an error.

#### Scenario: Low confidence
- GIVEN `motivo_parada: "confianza_insuficiente"`
- WHEN response renders
- THEN an info-styled blue box shows the abstention text
- AND no error styles are applied

### FR-8: Error Display
422 and 503 errors MUST display a distinct message in an error-styled box.

#### Scenario: 503 service error
- GIVEN POST /consulta returns 503
- WHEN the error is received
- THEN a red error box shows "Servicio no disponible"
- AND the input stays enabled for retry

### NFR-1: Clinical Design
The UI MUST use a sober palette — muted blues (#1a365d, #2b6cb0), grays, whites. MUST NOT use chatbot aesthetics (bright colors, bubbles, avatars).

### NFR-2: XSS Prevention
The system MUST run all respuesta HTML through DOMPurify.sanitize() before DOM insertion.

#### Scenario: Script injection blocked
- GIVEN respuesta contains `<script>alert('xss')</script>`
- WHEN rendered via DOMPurify
- THEN only safe HTML reaches the DOM
- AND no script executes

### NFR-3: Cold Start UX
The loading message SHOULD differentiate first-request delay from processing time.

#### Scenario: First request hint
- GIVEN no prior requests in this session
- WHEN the first POST is sent
- THEN the spinner says "Iniciando motor clínico…"
- AND subsequent requests show "Procesando consulta…"
