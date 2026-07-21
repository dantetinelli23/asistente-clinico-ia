# Compilado de Aprendizaje — Proyecto Final AI Engineering

**Sistema:** Asistente Clínico IA — Sistema de IA en producción **Stack:** Python · LangChain · LangGraph · FastAPI · Docker **Autor:** Dante Tinelli

---

## Cómo está armado este documento

Este es el documento de aprendizaje del Proyecto Final: un **documento vivo** al que le vamos sumando un checkpoint cada vez que terminamos una fase del proyecto. No es la entrega de la consigna (eso es un documento aparte, más seco); esto es tu material de estudio y, sobre todo, la **memoria externa** del proyecto. Como el proyecto es largo y la ventana de contexto del chat se va comprimiendo con el tiempo, este archivo —junto con el código en GitHub— es la fuente de verdad para retomar sin perder nada de lo construido.

A diferencia de los compilados de tus otros cursos, este **no tiene bloque de teoría de cátedra**. El Proyecto Final no trae material teórico: lo que documentamos acá es la **elaboración del sistema** —qué construimos, por qué tomamos cada decisión, el código clave, los problemas que aparecieron y cómo los resolvimos—, con el mismo nivel de detalle, las mismas metáforas y los mismos "porqués" de siempre. Todo es teoría-y-práctica del ejercicio.

Está organizado **por fases del proyecto** (no por el orden en que fue saliendo la charla). Cada checkpoint nuevo se agrega como una fase más al final, sin tocar lo anterior. El código completo vive en el repositorio; acá van los **fragmentos clave comentados** más la explicación, para que el documento sirva para *entender*, no para ser una fotocopia del repo.

---

## Índice

- [Fase 1: Setup del repositorio y el entorno](#fase-1-setup-del-repositorio-y-el-entorno)  
  - [Git y el control de versiones](#git-y-el-control-de-versiones)  
  - [La estructura de carpetas](#la-estructura-de-carpetas)  
  - [El gitignore y los secretos](#el-gitignore-y-los-secretos)  
  - [El entorno virtual](#el-entorno-virtual)  
  - [pip y el requirements](#pip-y-el-requirements)  
  - [Conectar el repo con GitHub](#conectar-el-repo-con-github)  
- [Fase 2: El sistema RAG sobre protocolos clínicos](#fase-2-el-sistema-rag-sobre-protocolos-clínicos)  
  - [Qué construimos: el pipeline completo](#qué-construimos-el-pipeline-completo)  
  - [Decisión de diseño: nube vs local y la privacidad](#decisión-de-diseño-nube-vs-local-y-la-privacidad)  
  - [Build once vs query many](#build-once-vs-query-many)  
  - [El parseo del documento](#el-parseo-del-documento)  
  - [La limpieza del corpus](#la-limpieza-del-corpus)  
  - [El chunking semántico y el problema del tamaño](#el-chunking-semántico-y-el-problema-del-tamaño)  
  - [El indexado en la base vectorial](#el-indexado-en-la-base-vectorial)  
  - [La búsqueda híbrida](#la-búsqueda-híbrida)  
  - [El reranking](#el-reranking)  
  - [La generación con el LLM](#la-generación-con-el-llm)  
  - [El diagrama del pipeline completo](#el-diagrama-del-pipeline-completo)  
- [Consideraciones de producción](#consideraciones-de-producción)  
- [Notas críticas](#notas-críticas)  
- [Glosario](#glosario)  
- [Estado del proyecto y próximos pasos](#estado-del-proyecto-y-próximos-pasos)

---

## Fase 1: Setup del repositorio y el entorno

Antes de escribir una sola línea de código, hay que **montar el taller**. La metáfora que ordena toda esta fase: es como preparar la cocina antes de cocinar. Si no tenés las ollas, la mesada y los ingredientes en su lugar, después es un caos. Un ingeniero prepara tres cosas antes de empezar: una carpeta ordenada para el proyecto, el control de versiones para no perder nunca nada, y un entorno aislado para las librerías.

### Git y el control de versiones

**Qué es git, con metáfora.** Imaginá un videojuego donde podés "guardar partida" en cualquier momento y volver a cualquier punto guardado si algo sale mal. Git es exactamente eso para tu código. Cada "guardado" se llama un **commit**: una foto del proyecto entero en ese instante.

El repositorio no es más que una carpeta que git vigila. Se activa con:

git init

Esto no hace nada visible dramático; solo le dice a git "empezá a vigilar esta carpeta". A partir de ahí, git puede tomar fotos cuando se lo pidas.

**Sacar una foto son dos gestos**, no uno. Primero *elegís* qué entra en la foto (el **staging**), y después *sacás* la foto (el **commit**). La metáfora: staging es acomodar a la familia para la foto; el commit es apretar el botón de la cámara.

git add .

git commit \-m "Estructura inicial del repositorio"

El `.` en `git add .` significa "todo lo que cambió". El `-m` es el mensaje: cada foto lleva una etiqueta que explica qué cambió. **Un buen mensaje de commit está escrito para que el vos-del-futuro, dentro de tres meses, entienda de un vistazo qué se hizo sin abrir los archivos.** Es el diario técnico del proyecto.

Antes de cada commit conviene mirar qué va a entrar con `git status`, que muestra en verde/rojo lo que cambió. Ese chequeo es también el reflejo de seguridad número uno cuando trabajás con secretos: mirar que en esa lista **no aparezcan** `.env`, `venv/` ni las bases locales.

### La estructura de carpetas

La consigna del Proyecto Final pide una carpeta por componente. En vez de crearlas a mano una por una, se las pedimos a la terminal de un saque:

mkdir retrieval, ranking, orquestacion, agente, adaptadores\_mcp, observabilidad, despliegue

`mkdir` significa "make directory" (crear carpeta). Cada carpeta es un **órgano** del sistema, y sale de un módulo del curso: `retrieval` y `ranking` son el RAG; `orquestacion` son las cadenas LCEL; `agente` es el grafo cíclico; `adaptadores_mcp` son las conexiones seguras; `observabilidad` son las métricas; `despliegue` es el empaquetado. La idea rectora del Proyecto Final: no inventamos órganos nuevos, **ensamblamos** los que ya construimos en cada módulo y les ponemos piel (una API) para que el mundo los pueda tocar.

**Un detalle no obvio:** git **no fotografía carpetas vacías**. Para que las carpetas recién creadas no desaparezcan del repo, se mete en cada una un archivo vacío llamado `.gitkeep`, cuya única función es que la carpeta deje de estar vacía y git la tome. Es un truco estándar de toda la industria.

También se separó una carpeta `data/` para las **fuentes crudas** (el PDF de la guía). El criterio: `data/` guarda la materia prima, y las carpetas de código guardan los programas que la trabajan. Mantener separado el dato del código que lo procesa ordena cualquier proyecto serio.

### El gitignore y los secretos

Hay cosas que **nunca** deben subir a un repositorio. El `.gitignore` es una lista de "cosas que git tiene que ignorar y no fotografiar jamás". Las dos más importantes:

- El **`.env`**, donde viven las API keys. Si eso llega a GitHub, cualquiera en el mundo puede ver tus claves y gastarte la plata de tus cuentas. Es *la* regla de oro de seguridad: **los secretos jamás van al repo.**  
- El **entorno virtual** (`venv`) y las **bases locales** (`chroma_db`, índices), porque pesan mucho y **se regeneran solos**. Subir el `venv` es como mandar por mail el electrodoméstico entero cuando alcanzaba con mandar la lista para comprarlo.

El `.gitignore` de este proyecto ignora, entre otros: `venv/`, `.env`, `__pycache__/`, `*.db`, `chroma_db/`, y los índices vectoriales. La regla mental: **todo lo que se puede regenerar corriendo un script, o todo lo que es secreto, va al `.gitignore`.**

La prueba de que funciona: al correr `git status` antes de un commit, esos archivos **no aparecen** en la lista. Esa ausencia es una buena noticia, no un error.

### El entorno virtual

Un entorno virtual es una **burbuja** de Python solo para este proyecto. La metáfora: es como tener una mesada de cocina separada por proyecto, para que los ingredientes (las librerías) de uno no se mezclen ni peleen con los de otro. Sin esto, todas las librerías de todos tus proyectos viven amontonadas y tarde o temprano una versión de una choca con otra.

Se crea y se activa así (en Windows / PowerShell):

python \-m venv venv

.\\venv\\Scripts\\Activate.ps1

La señal de que estás **adentro** de la burbuja es que aparece `(venv)` al principio de la línea de la terminal. Ese `(venv)` hay que verlo siempre antes de instalar librerías o correr código, para garantizar que todo cae adentro del proyecto y no desparramado por la máquina.

**Trampa clásica de Windows:** la activación puede fallar con un error de "running scripts is disabled on this system". Es una protección de Windows, no un error propio. Se resuelve una sola vez con:

Set-ExecutionPolicy \-ExecutionPolicy RemoteSigned \-Scope CurrentUser

### pip y el requirements

**Qué es pip.** Python viene "pelado": trae lo básico, pero las herramientas especializadas hay que traerlas de un depósito gigante en internet (PyPI). `pip` es el repartidor que va a ese depósito, busca la librería y la deja instalada adentro de la burbuja. Cada librería es una caja de herramientas ya hecha por otra gente.

**Qué es `requirements.txt`.** En vez de pedir las librerías una por una, escribimos la lista de compras en un archivo y le decimos a pip "traé todo lo de esta lista":

pip install \-r requirements.txt

La ventaja enorme: cualquiera que clone el repo corre un solo comando y arma el mismo entorno idéntico. Es la lista de ingredientes de la receta, y **crece a medida que el proyecto suma herramientas**: cada vez que se agrega una librería, se anota en `requirements.txt` y se reinstala. Así el archivo siempre refleja la verdad del proyecto.

**El smoke test.** Antes de escribir código de verdad, conviene probar las importaciones en seco (`python -c "import ..."`). Es un truco de oficio: si algo falta, lo detectás ahora y no en medio de un programa.

### Conectar el repo con GitHub

Hasta acá el proyecto vive solo en la máquina. GitHub es la nube donde se suben las fotos para respaldarlas y que otros las vean. El flujo tiene dos mitades: crear el repositorio vacío en la web de GitHub (con el mouse), y conectar la carpeta local con ese repo (con la terminal).

git remote add origin https://github.com/USUARIO/asistente-clinico-ia.git

git branch \-M main

git push \-u origin main

Pieza por pieza:

- `git remote add origin URL` → agrega una conexión a un repositorio remoto. `origin` es el **apodo** convencional del remoto principal (para no escribir la URL larga cada vez).  
- `git branch -M main` → nombra la rama principal `main`. La *rama* es la línea principal de trabajo; históricamente se llamaba `master`, hoy el estándar es `main`.  
- `git push -u origin main` → sube (empuja) las fotos al remoto. El `-u` deja enlazada la rama local con la remota, así **la próxima vez alcanza con `git push` a secas**.

La primera vez, Windows abre un login del navegador (Git Credential Manager) y guarda las credenciales; nunca más lo pide.

**Decisión tomada:** el repo es **público**, porque el objetivo es de portfolio (que la gente lo mire). Público es para *ver*, no para *modificar*: nadie puede tocar el repo sin permiso. Los secretos siguen a salvo porque el `.env` nunca sube.

---

## Fase 2: El sistema RAG sobre protocolos clínicos

Esta es la primera pieza de sustancia del sistema: el RAG (Retrieval-Augmented Generation) sobre protocolos clínicos reales. Cubre las carpetas `retrieval/` y `ranking/`, y corresponde conceptualmente a las Prácticas \#1 (Hybrid Search), \#2 (Re-ranking y chunking) y arranca la \#3 (LCEL).

### Qué construimos: el pipeline completo

RAG es el patrón de no confiar en el conocimiento interno del LLM (que puede estar desactualizado o alucinar), sino **forzarlo a apoyarse en documentos reales y verificables**. El pipeline completo tiene siete pasos, y se divide en dos momentos:

1. **Parsear** el PDF → sacar el texto crudo.  
2. **Limpiar** el corpus → quitar el ruido (bibliografía, índice, números de página).  
3. **Trocear (chunking)** → cortar el texto en pedazos coherentes.  
4. **Embeder e indexar** → convertir cada pedazo en vector y guardarlo en una base vectorial.  
5. **Buscar (híbrido)** → traer candidatos por significado \+ por palabras.  
6. **Rerankear** → reordenar los candidatos con un modelo más fino.  
7. **Generar** → el LLM redacta la respuesta apoyándose solo en lo recuperado.

### Decisión de diseño: nube vs local y la privacidad

Una de las decisiones más importantes del sistema, y la que le da criterio "de producción". El insight clave: **no todos los datos del sistema son igual de sensibles.** Hay dos corrientes de datos distintas:

- **Los protocolos clínicos** (las guías que el sistema consulta): son **conocimiento institucional**, no tienen datos personales de nadie. El nombre de un paciente no aparece en un protocolo de HTA. Por eso **sí pueden ir a una API externa** (Cohere) sin violar ninguna privacidad.  
- **Las historias clínicas** (la base SQL de pacientes): *acá* están los datos sensibles. Estos no pueden salir de la infraestructura.

La metáfora: es una biblioteca médica dentro de un hospital. Los libros de la biblioteca (los protocolos) los puede fotocopiar cualquiera. Pero las fichas de los pacientes están bajo llave y no salen del edificio.

**Decisión concreta:** el RAG sobre protocolos usa **Cohere por API** (embeddings `embed-multilingual-v3.0` y rerank `rerank-v3.5`), porque los protocolos no son sensibles y así el despliegue queda liviano y reproducible. En la Práctica \#8 se habían usado modelos **locales** (HuggingFace \+ BGE) por privacidad; para un repo que tiene que correr barato en Cloud Run, los modelos locales pesan cientos de megas e inflan el arranque en frío. Queda documentado que un despliegue clínico real *on-premise* cambiaría Cohere por modelos locales (de hecho, la Trial de Cohere es no comercial, lo que refuerza que en producción se autohospedaría).

El puente con los cursos anteriores: la idea de RAG, embeddings, base vectorial y reranking ya sonaba de n8n. Lo nuevo de este curso es **escribirlo por dentro, en código**, en vez de que lo haga un nodo.

### Build once vs query many

Una distinción que ordena todo el RAG: los pasos de armar el índice (parsear, limpiar, trocear, embeder) se hacen **una sola vez**; los pasos de buscar (híbrido, rerank, generar) se hacen **cada vez que alguien pregunta**.

La metáfora: armar el índice es como ordenar y catalogar toda una biblioteca (lo hacés una vez, es trabajoso). Buscar es ir a buscar un libro puntual (lo hacés mil veces, es rápido porque ya está catalogado). Por eso son archivos distintos: `parsear.py` e `indexar.py` son "build once"; `buscar_*.py` y `generar.py` son "query many".

### El parseo del documento

**Por qué no alcanza con `pypdf`.** El primer intento leyó el PDF con `pypdf`, que solo "arranca" el texto plano. El resultado fue **texto sucio**: números de página en el medio, encabezados repetidos, tablas aplastadas en una línea rara. Eso no es un error del código: es cómo sale el texto crudo de un PDF real del Estado.

**La solución: parsear a Markdown limpio.** Se eligió `pymupdf4llm`, un parser que corre **100% local** (sin nube, sin API key) y convierte el PDF a Markdown respetando títulos, listas y tablas. Se evaluó también LlamaParse (más potente para PDFs infernales), pero está en plena migración de paquetes y agrega otra dependencia de nube; como la guía es densa en texto (no un escaneo ni multicolumna complejo), un parser local rinde casi igual y mantiene la historia de privacidad más limpia.

Fragmento clave (`retrieval/parsear.py`):

import pymupdf4llm

texto\_markdown \= pymupdf4llm.to\_markdown("data/guia\_hta.pdf")

with open("data/guia\_hta.md", "w", encoding="utf-8") as archivo:

    archivo.write(texto\_markdown)

Conceptos: `import pymupdf4llm` trae la **caja entera** (por eso después se usa `pymupdf4llm.to_markdown`, con el `.` como "de"). El patrón `with open(..., "w", encoding="utf-8") as archivo:` abre un archivo para **escribir** (`"w"`), y el `encoding="utf-8"` es obligatorio en español para que las tildes y la ñ no salgan rotas. El `with` garantiza que el archivo se cierre solo al terminar (como una heladera que se cierra sola).

**Patrón inteligente:** parsear es un paso caro que se hace una vez. El resultado limpio se **guarda en disco** (`data/guia_hta.md`), así no hay que reparsear cada vez que se ajusta el chunking.

### La limpieza del corpus

Este fue uno de los aprendizajes más importantes de la fase, y salió de un problema real: las primeras búsquedas traían **bibliografía, el índice y números de página** en vez de contenido clínico.

**El principio: garbage in, garbage out.** Un RAG es tan bueno como lo que se le mete adentro. Meter la bibliografía, el índice y los pies de página no solo no suma: **resta**, porque son chunks que el buscador puede traer por error en lugar de la respuesta clínica. En la industria, sacar este ruido antes de indexar se llama **curar** o **limpiar el corpus**, y es trabajo real, no opcional.

Se limpiaron tres tipos de ruido:

1. **La bibliografía** (la lista de referencias al final) → se borró a mano del `.md`.  
2. **El índice / tabla de contenidos** del principio (títulos con números de página) → se borró a mano.  
3. **Los números de página sueltos** (pie de página, tipo `**_38_**`), que estaban salpicados en cada una de las 40 páginas → se borraron automáticamente con una **expresión regular (regex)**.

Fragmento clave del limpiado con regex (`retrieval/parsear.py`):

import re

patron\_numero\_pagina \= r"^\\s\*\\\*\*\_\*\\d{1,3}\_\*\\\*\*\\s\*$"

texto\_limpio \= re.sub(patron\_numero\_pagina, "", texto\_markdown, flags=re.MULTILINE)

**Qué es una regex:** un patrón que se le describe a la computadora para que busque (y borre) automáticamente todo lo que coincide, en todo el documento. El patrón de arriba se lee: *"una línea que, de punta a punta, no tiene nada más que un número de hasta 3 cifras, opcionalmente decorado con `**` o `_`"*. Pieza por pieza: `^` es el principio de línea, `\d{1,3}` es de 1 a 3 dígitos, `$` es el final de línea. Como el número tiene que estar **solo en toda la línea**, el patrón no toca un "140/90" que forma parte de una frase real. `re.sub(patron, "", texto, flags=re.MULTILINE)` busca y reemplaza por vacío; el flag `MULTILINE` hace que `^` y `$` apliquen a **cada línea**, no solo al documento entero.

**Nota:** este patrón agarra los números que están solos en su línea. Algún número de página que quedó pegado en la misma línea que texto real puede escaparse; es un caso límite conocido y menor.

### El chunking semántico y el problema del tamaño

**Qué es el chunking y por qué importa tanto.** Trocear es el paso que más define la calidad del RAG. Se usó **chunking semántico**: cortar donde cambia el *significado*, no cada N caracteres a lo bruto. La herramienta es `SemanticChunker`, que mide cuándo el significado de una frase a la otra cambia mucho y ahí corta. El puente con la Práctica \#2: en vez de cortar cada 1000 caracteres partiendo ideas a la mitad, corta por tema, así ningún pedazo queda partido en medio de una idea.

**El equilibrio del tamaño del chunk.** Los dos extremos son malos:

- **Muy grande:** mete varias ideas juntas. Su vector queda como un "promedio borroso" de varios temas, así que matchea peor con las preguntas; y cuando se lo trae, arrastra ruido.  
- **Muy chico:** pierde contexto; una frase suelta puede no entenderse sola.  
- **El punto justo:** una idea coherente por chunk — grande para entenderse solo, enfocado para ser preciso.

**El problema real que apareció.** Un script de diagnóstico reveló que el chunk que contenía la respuesta buscada tenía **19.346 caracteres** (8-10 páginas en un solo chunk). El `SemanticChunker` no tiene tope de tamaño por defecto: si un tramo mantiene un "tema" parecido según su medición, lo deja entero. Ese chunk gigante era la causa de que la búsqueda fallara: su vector era un batido borroso de diez temas, y no matcheaba con la pregunta precisa aunque el dato estuviera adentro.

**La solución: un splitter de dos etapas.** Primero el semántico corta por tema; después, un segundo splitter parte a la fuerza cualquier chunk que se haya pasado de un límite de tamaño. Es un patrón real: "cortá por significado, y donde el significado no alcance, cortá por tamaño como red de seguridad".

Fragmento clave (`retrieval/indexar.py`):

from langchain\_text\_splitters import RecursiveCharacterTextSplitter

troceador\_semantico \= SemanticChunker(embeddings)

chunks\_semanticos \= troceador\_semantico.create\_documents(\[texto\_completo\])

troceador\_de\_respaldo \= RecursiveCharacterTextSplitter(

    chunk\_size=1000,

    chunk\_overlap=200,

)

chunks \= troceador\_de\_respaldo.split\_documents(chunks\_semanticos)

Conceptos: `RecursiveCharacterTextSplitter` corta por cantidad de caracteres, pero de forma inteligente (intenta cortar en saltos de párrafo, luego de línea, luego de espacio, sin partir palabras). `chunk_size=1000` es el tope de tamaño. `chunk_overlap=200` hace que, al partir un chunk, se repitan los últimos 200 caracteres al principio del siguiente, para que una idea cortada al medio conserve contexto en ambos lados. Clave: se le pasa `chunks_semanticos` (no el texto crudo), así conserva los buenos cortes del semántico y solo interviene donde un chunk salió gigante.

**Resultado:** de un chunk de 19.346 caracteres se pasó a 113 chunks de tamaño sano (el que tenía la respuesta bajó a \~741 y \~998 caracteres). Esto arregló la búsqueda.

### El indexado en la base vectorial

Se usa **Chroma** como base vectorial (local, gratis, persiste en disco). El indexado convierte cada chunk en vector con los embeddings de Cohere y lo guarda.

Fragmento clave (`retrieval/indexar.py`):

base\_vectorial \= Chroma.from\_documents(

    documents=chunks,

    embedding=embeddings,

    persist\_directory="chroma\_db",

)

`persist_directory="chroma_db"` es lo que hace que la base quede **guardada en disco**, así no hay que reconstruirla cada vez (es el "build once"). Esa carpeta está en el `.gitignore` porque se regenera.

**Aprendizaje clave: `from_documents` agrega, no reemplaza.** Si se re-indexa sin borrar la carpeta `chroma_db` vieja, los chunks nuevos se **suman** a los viejos, y quedan mezclados (por ejemplo, chunks del texto sucio conviviendo con los del texto limpio). Es un problema silencioso: no tira error, pero contamina los resultados. Por eso el ciclo correcto es siempre **borrar `chroma_db` primero, después re-indexar**. La metáfora: catalogar los libros nuevos encima de los viejos sin sacar los que ya no sirven deja la biblioteca contaminada. En un sistema serio, esto se automatiza con una línea que limpia la base antes de reconstruir.

### La búsqueda híbrida

Es el tema estrella de la Práctica \#1, ahora escrito por dentro. Se combinan **dos formas de buscar**:

- **Búsqueda densa (por significado):** convierte la pregunta en vector y trae los chunks cuyo *significado* se parece, aunque no compartan palabras.  
- **Búsqueda por palabras (BM25):** coincidencia literal de términos, sin interpretar.

La metáfora: son dos bibliotecarios. Uno entiende de qué *tema* le hablás aunque uses otras palabras (el denso); el otro es un rastreador literal que encuentra la palabra exacta (BM25). Cada uno falla donde el otro brilla: el denso puede perderse un nombre de droga poco común, y el literal no entiende sinónimos. **Búsqueda híbrida** es ponerlos a trabajar juntos y fusionar sus resultados.

Fragmento clave (`retrieval/buscar_hibrido.py`):

buscador\_denso \= base\_vectorial.as\_retriever(search\_kwargs={"k": 5})

todos\_los\_chunks \= base\_vectorial.get()\["documents"\]

buscador\_bm25 \= BM25Retriever.from\_texts(todos\_los\_chunks)

buscador\_bm25.k \= 5

buscador\_hibrido \= EnsembleRetriever(

    retrievers=\[buscador\_denso, buscador\_bm25\],

    weights=\[0.5, 0.5\],

)

Conceptos: `.as_retriever(search_kwargs={"k": 5})` convierte la base en un buscador que trae los 5 más parecidos (`k` \= cuántos vecinos). BM25 no vive en Chroma: se reconstruye en memoria a partir de los textos (para este tamaño de documento es instantáneo). `EnsembleRetriever` fusiona ambos con `weights=[0.5, 0.5]` (mitad y mitad). Por debajo usa **Reciprocal Rank Fusion (RRF)**: en vez de mezclar los puntajes crudos (que no son comparables entre buscadores), fusiona por la **posición** en la que cada uno rankeó cada resultado. Es la forma estándar de combinar buscadores distintos sin que uno gane injustamente por tener números en otra escala.

**Detalle no obvio:** `k=5` en cada buscador **no** da 10 candidatos únicos. El `EnsembleRetriever` fusiona por ranking, y es común que el mismo chunk aparezca en el top de ambos (si es bueno, el denso lo ve relevante por significado *y* el BM25 por palabras). Cuando eso pasa, cuenta como **uno solo**. Por eso el pool real de candidatos suele ser menor que la suma.

### El reranking

La búsqueda híbrida es rápida pero "gruesa": trae candidatos razonables sin *leer* de verdad cada uno contra la pregunta. El **reranker** es un modelo más lento pero mucho más fino: toma la pregunta y cada candidato y los lee juntos, par por par, para juzgar cuál responde mejor.

La metáfora: un primer bibliotecario rápido agarra 9 libros que *suenan* relacionados; un segundo bibliotecario, más leído, hojea esos 9 y dice cuál responde tu pregunta específica. Por eso el pipeline es híbrido *primero* (traer ancho, no perderse nada) y reranking *después* (ordenar fino lo que ya se trajo).

Fragmento clave (`retrieval/buscar_con_rerank.py`):

reranker \= CohereRerank(model="rerank-v3.5", top\_n=3)

buscador\_final \= ContextualCompressionRetriever(

    base\_compressor=reranker,

    base\_retriever=buscador\_hibrido,

)

Conceptos: `CohereRerank(model="rerank-v3.5", top_n=3)` crea el reranker y le pide quedarse con los 3 mejores tras reordenar. `ContextualCompressionRetriever` es la pieza que combina un buscador base (el híbrido) con un "compresor" (el reranker): recibe los candidatos del híbrido, se los pasa al reranker para que los reordene y filtre, y devuelve el resultado final. Es el mismo patrón de la cafetera, pero ensamblado sobre el híbrido en vez de un buscador simple (matrioshkas).

Cada resultado trae un `relevance_score` (0 a 1\) en su `metadata`, que dice qué tan relevante juzgó el reranker a ese chunk. Es oro para depurar.

**Criterio de tuning:** conviene darle al reranker **más candidatos crudos** (subir `k` del híbrido) para que tenga de dónde elegir, y filtrar angosto al final (`top_n` chico). "Buscar ancho, filtrar angosto." El reranker solo puede reordenar lo que le llega: si el chunk bueno no entró al pool en la etapa híbrida, no hay reranker que lo rescate.

### La generación con el LLM

El paso que convierte el "buscador" en un "RAG" de verdad: se le manda al LLM la pregunta **junto con** los chunks recuperados, y se le pide responder **basándose solo en eso**.

Se usa **Gemini** (`gemini-2.5-flash-lite`) vía `langchain_google_genai`, el mismo modelo del grafo de la Práctica \#10, para mantener el sistema consistente.

Fragmento clave del armado del contexto y la cadena (`retrieval/generar.py`):

contexto \= "\\n\\n".join(doc.page\_content for doc in chunks\_encontrados)

plantilla \= ChatPromptTemplate.from\_messages(\[

    ("system", "... instrucciones ...\\n\\nCONTEXTO:\\n{contexto}"),

    ("human", "{pregunta}"),

\])

llm \= ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)

cadena \= plantilla | llm

respuesta \= cadena.invoke({"contexto": contexto, "pregunta": pregunta})

Conceptos nuevos, que son el corazón de **LCEL** (LangChain Expression Language, tema de la Práctica \#3):

- `"\n\n".join(doc.page_content for doc in chunks_encontrados)` pega el texto de los chunks en un solo bloque, separados por una línea en blanco. Ese bloque es el "contexto".  
- `ChatPromptTemplate.from_messages([...])` es una plantilla de conversación con **espacios en blanco** (`{contexto}`, `{pregunta}`) que se rellenan después. El mensaje `"system"` son las instrucciones de fondo; el `"human"` es la pregunta del usuario. Las llaves son *placeholders*, el mismo mecanismo que los f-strings de Python.  
- `temperature=0` fija la mínima creatividad/aleatoriedad: en clínica se quiere consistencia y apego a los datos, no creatividad.  
- `cadena = plantilla | llm` — el **pipe** `|` es el símbolo que da nombre a LCEL. Se lee como en la terminal de Linux: "la salida de la izquierda entra como entrada a la derecha". Primero se rellena la plantilla, y el prompt armado se manda al LLM. Es el prompt chaining de Agentes, con sintaxis nueva.  
- `.invoke({...})` dispara la cadena completa. El resultado trae la respuesta en `.content`.

**El system prompt, con estructura de "manual de operaciones" (los siete bloques de Agentes).** El primer prompt de prueba era demasiado básico. Se reescribió con bloques rotulados: **ROL** (asistente para profesionales, no para pacientes), **FUENTE DE VERDAD** (solo el contexto, prohibido usar conocimiento médico propio — la instrucción anti-alucinación más importante), **REGLAS DE RESPUESTA** (no inventar; si el contexto no alcanza, decirlo; citar valores exactos; distinguir umbrales por método de medición), **SEGURIDAD CLÍNICA** (advertir si hay signos de urgencia), y **FORMATO** (prosa clara, sin sobre-estructurar).

**Alcance del prompt vs. el grafo.** Este prompt *advierte* sobre urgencias dentro de su respuesta, pero el bloqueo automático real ("si es urgencia, no respondas y escalá a un humano") es más grande que un prompt: necesita revisar la pregunta *antes* de buscar y evaluar la respuesta *después* de generar. Eso es trabajo del **grafo cíclico** de la Fase 3, no de este script. Cada pieza hace su trabajo; no se sobrecarga el prompt con lo que le toca al grafo.

**Resultado validado:** ante "¿desde qué valores de presión se considera hipertensión?", el sistema respondió distinguiendo los cuatro métodos de medición (consultorio 140/90, MAPA diurno/nocturno/24h, MDPA), citando los valores exactos, sin alucinar, y convirtiendo la tabla Markdown en prosa legible. Es un RAG clínico funcionando de punta a punta.

### El diagrama del pipeline completo

  DOCUMENTO CRUDO (guia\_hta.pdf)

           |

           v

   ┌──────────────────┐

   │  BUILD ONCE       │   (se corre una sola vez)

   │                   │

   │  parsear.py       │   PDF \-\> Markdown limpio (pymupdf4llm, local)

   │      |            │

   │      v            │   \+ limpieza de corpus (regex, borrado manual)

   │  indexar.py       │

   │      |            │

   │      \+-- chunking semantico (SemanticChunker)

   │      \+-- tope de tamaño     (RecursiveCharacterTextSplitter 1000/200)

   │      \+-- embeddings         (Cohere embed-multilingual-v3.0)

   │      v            │

   │   \[ chroma\_db \]   │   base vectorial persistida en disco

   └──────────────────┘

           |

           v

   ┌────────────────────────────────────────────────┐

   │  QUERY MANY       (cada vez que alguien pregunta)│

   │                                                  │

   │   pregunta                                       │

   │      |                                            │

   │      v                                            │

   │   BUSQUEDA HIBRIDA                                 │

   │   ┌─────────────┐   ┌─────────────┐               │

   │   │ denso (k=5) │   │ BM25 (k=5)  │               │

   │   └──────┬──────┘   └──────┬──────┘               │

   │          └────── RRF ──────┘   (EnsembleRetriever)│

   │                  |                                 │

   │                  v                                 │

   │   RERANK  (Cohere rerank-v3.5, top\_n=3)            │

   │                  |                                 │

   │                  v                                 │

   │   GENERACION  (Gemini \+ prompt anclado al contexto)│

   │                  |                                 │

   │                  v                                 │

   │             RESPUESTA                              │

   └────────────────────────────────────────────────┘

---

## Consideraciones de producción

Notas de "esto en el mundo real se haría así", que sirven para la documentación del entregable final:

- **Modelos locales para datos sensibles.** El RAG de protocolos usa Cohere (nube) porque los protocolos no son sensibles. En un despliegue clínico real, los datos de pacientes obligarían a usar embeddings y reranker **locales/on-premise** (o enmascarar la PII antes de que toque un modelo externo). La Trial de Cohere, además, es de uso no comercial, lo que refuerza que producción real se autohospedaría.  
    
- **Los rerankers y las tablas.** Se observó que el reranker de Cohere le da menor puntaje a una **tabla** (criterios diagnósticos PAS/PAD) que a la misma información en prosa, aunque la tabla sea clínicamente la respuesta más precisa. Es una limitación conocida: los rerankers "leen" mejor prosa que contenido tabular. En un RAG clínico, donde las tablas de criterios y dosis son críticas, convendría reforzarlas (por ejemplo, convertir tablas a prosa antes de indexar, o darles un boost).  
    
- **Limpieza automática de la base al re-indexar.** Hoy se borra `chroma_db` a mano antes de re-indexar. En un sistema serio, `indexar.py` limpiaría la base al arranque para no depender de la memoria del que corre el script.  
    
- **El formato del prompt no es garantía.** Las instrucciones de formato en el system prompt son "fuertes sugerencias", no garantías (el LLM usó viñetas donde se le pidió prosa, aun con `temperature=0`). Cuando el formato importa de verdad (salida que otro programa parsea), hay que forzarlo con **structured output**, no pedirlo en el prompt.  
    
- **BM25 en memoria.** Para este documento, reconstruir BM25 en memoria en cada corrida es instantáneo. En un corpus gigante se optimizaría (persistir el índice BM25), pero no era el caso.

---

## Notas críticas

- La consigna del Proyecto Final está escrita a escala empresa (Kubernetes, Arize, MCP, serverless, todo junto). La decisión de scope fue **consolidar lo ya construido en un repo coherente** y elegir una historia de despliegue realista (Docker \+ Cloud Run), documentando Kubernetes como arquitectura en vez de levantarlo de verdad. Distinguir "lo que corre" de "lo que se documenta como diseño" es criterio senior, no una limitación.  
    
- El código clínico de la Práctica \#8 (MCP) no estaba entre los archivos disponibles, así que el sistema es un **pivot a clínico** de la maquinaria de tickets/cafetera ya construida, no un ensamblado de un sistema clínico preexistente. Esto es mejor para el aprendizaje: se entiende y se toca cada línea.

---

## Glosario

- **RAG (Retrieval-Augmented Generation):** patrón que hace que el LLM responda apoyándose en documentos recuperados en vez de en su conocimiento interno.  
- **Chunk:** un pedazo de texto en que se corta un documento para indexarlo.  
- **Chunking semántico:** trocear cortando donde cambia el significado, no por cantidad fija de caracteres.  
- **Embedding:** la conversión de un texto a un vector (una lista de números) que representa su significado.  
- **Base vectorial (Chroma):** base de datos que guarda embeddings y permite buscar por similaridad de significado.  
- **Búsqueda densa:** buscar por similaridad de vectores (significado).  
- **BM25:** algoritmo de búsqueda por coincidencia literal de palabras.  
- **Búsqueda híbrida:** combinar densa \+ BM25.  
- **RRF (Reciprocal Rank Fusion):** método para fusionar los rankings de varios buscadores por posición, no por puntaje crudo.  
- **Reranking:** reordenar los candidatos recuperados con un modelo más fino que lee pregunta y candidato juntos.  
- **`k`:** cuántos resultados trae un buscador.  
- **`top_n`:** cuántos resultados deja el reranker tras reordenar.  
- **`relevance_score`:** puntaje 0-1 que el reranker asigna a cada candidato.  
- **LCEL (LangChain Expression Language):** la forma de encadenar pasos en LangChain con el pipe `|`.  
- **Pipe (`|`):** operador que conecta la salida de un paso con la entrada del siguiente.  
- **`ChatPromptTemplate`:** plantilla de prompt con placeholders que se rellenan con datos.  
- **Placeholder:** un `{espacio}` en una plantilla que se reemplaza por un valor real.  
- **`temperature`:** parámetro del LLM que controla la aleatoriedad/creatividad (0 \= máximo apego a los datos).  
- **Parseo:** extraer el texto de un documento (acá, PDF → Markdown con `pymupdf4llm`).  
- **Regex (expresión regular):** patrón para buscar y reemplazar texto que coincide con una forma.  
- **Corpus:** el conjunto de documentos/texto que alimenta el RAG.  
- **Curar / limpiar el corpus:** sacar el ruido (bibliografía, índice, pies de página) antes de indexar.  
- **Build once / query many:** los pasos de indexar se hacen una vez; los de buscar, cada consulta.  
- **`.gitignore`:** lista de archivos que git no versiona (secretos, cosas regenerables).  
- **Commit:** una foto del proyecto en un instante.  
- **Push:** subir los commits al repositorio remoto (GitHub).  
- **Entorno virtual (venv):** burbuja aislada de librerías por proyecto.  
- **`requirements.txt`:** lista de librerías del proyecto para reinstalar el entorno idéntico.

---

## Estado del proyecto y próximos pasos

**Completado hasta este checkpoint:**

- **Fase 1 — Setup:** repositorio creado, estructura de carpetas, `.gitignore`, entorno virtual, `requirements.txt`, conectado a GitHub (público). ✅  
- **Fase 2 — RAG:** pipeline completo funcionando de punta a punta (parseo local → limpieza → chunking semántico con tope de tamaño → indexado en Chroma → búsqueda híbrida → reranking → generación anclada al contexto). ✅

**Archivos de código de esta fase (en `retrieval/`):** `parsear.py`, `indexar.py`, `ver_chunks.py`, `diagnostico.py`, `buscar_hibrido.py`, `buscar_con_rerank.py`, `generar.py`.

**Stack en uso:** Python · LangChain (+ classic, community, experimental) · Cohere (embeddings \+ rerank) · Chroma · BM25 · pymupdf4llm · Gemini (`gemini-2.5-flash-lite`).

**Próximo paso — Fase 3 (agente / grafo cíclico):** construir el `StateGraph` de LangGraph que orquesta todo con lógica de decisión: guardrail de seguridad (detectar urgencia y escalar a humano) → recuperar → generar → evaluar la respuesta → refinar o responder, con memoria (checkpointer) y tope de iteraciones. Ahí se integra el RAG de esta fase como una herramienta dentro del grafo, y se implementa de verdad el bloqueo por urgencia que hoy el prompt solo advierte.  
