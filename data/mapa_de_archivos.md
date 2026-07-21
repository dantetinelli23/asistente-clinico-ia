# Mapa de archivos del repositorio

Referencia viva de qué hace cada archivo y en qué categoría está. Se actualiza a medida que el proyecto crece. Sirve para que cualquiera (incluido el vos-del-futuro) entienda de un vistazo qué es código vivo del sistema, qué se corre una sola vez, qué es prueba y qué es borrador.

**Categorías:**

- **Producción** — código vivo del sistema; se ejecuta en cada consulta.  
- **Build once** — se corre a mano, una sola vez (o cuando cambia el documento fuente); prepara datos/índices.  
- **Prueba** — sirve para ejecutar o probar el sistema, no es parte del flujo productivo.  
- **Infra de paquete** — archivos técnicos que Python necesita para importar carpetas.  
- **Borrador** — andamios de aprendizaje de la Fase 2, ya reemplazados por la versión final; se conservan como registro (renombrados con prefijo `_borrador_`). No se usan.

---

## Carpeta `retrieval/` (el RAG)

| Archivo | Categoría | Qué hace |
| :---- | :---- | :---- |
| `parsear.py` | Build once | Convierte el PDF de la guía a Markdown limpio (`pymupdf4llm`, local) y limpia el ruido (números de página con regex). Deja `data/guia_hta.md`. |
| `indexar.py` | Build once | Lee el Markdown, lo trocea (chunking semántico \+ tope de tamaño) y arma la base vectorial `chroma_db` con embeddings de Cohere. |
| `buscador.py` | **Producción** | El corazón de la búsqueda. Arma una vez el buscador híbrido (denso \+ BM25) con reranking, y expone `buscar_protocolos(pregunta)` que el grafo usa en cada consulta. |
| `__init__.py` | Infra de paquete | Vacío. Le dice a Python que `retrieval` es un paquete importable. |
| `_borrador_ver_chunks.py` | Borrador | Inspeccionaba los chunks y sus tamaños. Sirvió para diagnosticar el chunk gigante. |
| `_borrador_diagnostico.py` | Borrador | `grep` para verificar si un dato estaba en la base. |
| `_borrador_buscar_hibrido.py` | Borrador | Primera versión, solo búsqueda híbrida. |
| `_borrador_buscar_con_rerank.py` | Borrador | Segunda versión, híbrido \+ rerank. |
| `_borrador_generar.py` | Borrador | Prueba del ciclo RAG completo con generación. Su lógica final vive hoy en `buscador.py` y en el nodo `generar` del grafo. |

## Carpeta `agente/` (el grafo cíclico)

| Archivo | Categoría | Qué hace |
| :---- | :---- | :---- |
| `estado.py` | **Producción** | Define `EstadoConsulta` (TypedDict): la "ficha" que viaja por todos los nodos del grafo. |
| `grafo.py` | **Producción** | El sistema central. Define los 7 nodos, la lógica de decisión, el ensamblado del grafo y su compilación con memoria. Expone `grafo`. |
| `llm_seguro.py` | **Producción** | La "centralita" única de acceso al LLM. Envuelve las llamadas a Gemini con manejo de error (degradación con gracia). Expone `invocar_llm`. |
| `probar_grafo.py` | Prueba | Ejecuta el grafo con una consulta de ejemplo para verlo funcionar de punta a punta. Punto de entrada de prueba. |
| `__init__.py` | Infra de paquete | Vacío. Le dice a Python que `agente` es un paquete importable. |

## Carpeta `data/` (fuentes crudas)

| Archivo | Categoría | Qué hace |
| :---- | :---- | :---- |
| `guia_hta.pdf` | Fuente | La guía clínica original (HTA 2026, Ministerio de Salud). Se versiona en el repo (público, no sensible). |
| `guia_hta.md` | Generado | El texto limpio que produce `parsear.py`. |

## Otras carpetas (todavía vacías, a completar)

`ranking/`, `orquestacion/`, `adaptadores_mcp/`, `observabilidad/`, `despliegue/` — creadas en la Fase 1 con un `.gitkeep`, se llenan en las fases siguientes.

## Raíz del proyecto

| Archivo | Categoría | Qué hace |
| :---- | :---- | :---- |
| `requirements.txt` | Config | Lista de librerías del proyecto. Crece con cada fase. |
| `.gitignore` | Config | Lista de lo que git no versiona (secretos y cosas regenerables). |
| `.env` | Secreto (NO se sube) | Las API keys (Cohere, Google). Ignorado por git. |
| `chroma_db/` | Generado (NO se sube) | La base vectorial. Se regenera con `indexar.py`. Ignorada por git. |
| `venv/` | Generado (NO se sube) | El entorno virtual. Ignorado por git. |

