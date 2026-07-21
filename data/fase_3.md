# Fase 3 — El agente cíclico (LangGraph)

Checkpoint de aprendizaje del Proyecto Final. Esta fase construye el "cerebro" que orquesta el RAG de la Fase 2 con lógica de decisión, memoria y resiliencia. Corresponde a las carpetas `agente/` y conceptualmente a las Prácticas \#5 y \#6 (grafos de estado y control de bucles).

## Índice

- [Qué construimos: de una cadena a un grafo](#qué-construimos-de-una-cadena-a-un-grafo)  
- [Los cinco conceptos de LangGraph](#los-cinco-conceptos-de-langgraph)  
- [El Estado: la ficha que viaja](#el-estado-la-ficha-que-viaja)  
- [La anatomía de un nodo](#la-anatomía-de-un-nodo)  
- [Salida estructurada con Pydantic](#salida-estructurada-con-pydantic)  
- [El replanteo del diseño clínico](#el-replanteo-del-diseño-clínico)  
- [El ensamblado del grafo](#el-ensamblado-del-grafo)  
- [Compilar con memoria: checkpointer y thread\_id](#compilar-con-memoria-checkpointer-y-thread_id)  
- [El problema de rutas e imports](#el-problema-de-rutas-e-imports)  
- [La resiliencia: manejar los fallos del LLM](#la-resiliencia-manejar-los-fallos-del-llm)  
- [El diagrama del grafo final](#el-diagrama-del-grafo-final)  
- [Consideraciones de producción](#consideraciones-de-producción)  
- [Glosario de esta fase](#glosario-de-esta-fase)  
- [Estado del proyecto](#estado-del-proyecto)

---

## Qué construimos: de una cadena a un grafo

En la Fase 2 el RAG terminaba en una **cadena** (`plantilla | llm`): una línea recta. Entra una pregunta, sale una respuesta, siempre el mismo camino. Es una cinta de montaje. El problema es que un asistente clínico serio necesita **decidir**: ¿esto es una urgencia? ¿la respuesta es lo bastante buena o la reintento? ¿me abstengo? Una línea recta no decide, ni vuelve atrás, ni se bifurca. Para eso hace falta un **grafo**.

La metáfora: la cadena es una **receta** que seguís de arriba a abajo, siempre igual. El grafo es un **GPS**: tiene un objetivo, pero en cada cruce vuelve a evaluar y puede recalcular la ruta, tomar un desvío, o volver a intentar si se topó con una calle cortada. El puente con Agentes es directo: el **loop ReAct** (razonar → actuar → observar → decidir si sigue) *es* un grafo cíclico. En Agentes se vio el concepto; acá se construye con nodos y flechas de verdad.

El puente maestro: el grafo de tickets de la Práctica \#10 ya era casi exactamente esta máquina. La Fase 3 fue **pivotearlo a clínico**, con tres cambios: el guardrail detecta urgencia clínica; el nodo de recuperar se conecta al RAG real de la Fase 2; y los prompts pasan a clínicos.

## Los cinco conceptos de LangGraph

1. **El Estado (`State`)** — la ficha clínica que viaja por todo el circuito. Un objeto compartido que cada nodo lee y escribe.  
2. **Los Nodos (`Node`)** — cada paso que hace un trabajo y actualiza la ficha. Son funciones.  
3. **Las Flechas (`Edge`)** — conectan un nodo con el siguiente, el camino fijo.  
4. **La Flecha Condicional (`conditional edge`)** — el cruce con decisión: una función mira la ficha y decide para dónde ir. Es lo que convierte una línea en un grafo.  
5. **El Ciclo y el Checkpointer** — el ciclo es una flecha que va para atrás (habilita iterar, con un tope); el checkpointer es la persistencia (guarda la ficha para que sobreviva entre turnos).

## El Estado: la ficha que viaja

El Estado es el **contrato compartido**: todos los nodos leen y escriben sobre él, así que se define antes que nada. La metáfora: un formulario con campos rotulados que viaja de mano en mano; cada campo espera un tipo de dato, arranca casi vacío, y cada nodo completa lo suyo.

from typing import TypedDict, List

class EstadoConsulta(TypedDict):

    consulta\_id: str

    pregunta: str             \# la pregunta actual (puede reformularse en el loop)

    pregunta\_original: str    \# lo que escribio el profesional (nunca cambia)

    documentos: List\[str\]

    respuesta: str

    intentos: int

    confianza: float

    es\_urgencia: bool

    escalado: bool

    resuelto: bool

    registrado: bool

    motivo\_parada: str

Conceptos: un **`TypedDict`** es un diccionario con **forma fija y tipada** — define qué claves existen y qué tipo lleva cada una (el formulario con campos ya impresos). Los *type hints* (`str`, `int`, `float`, `bool`, `List[str]`) documentan qué va en cada campo y ayudan a cazar errores.

La separación **`pregunta` vs `pregunta_original`** es astuta: `pregunta` se usa para buscar y puede cambiar cuando el loop la reformula; `pregunta_original` guarda lo que se preguntó de verdad y no se toca nunca (se usa para redactar la respuesta final). El campo **`es_urgencia`** es el nuevo campo clínico que no estaba en tickets.

## La anatomía de un nodo

Todos los nodos siguen el mismo molde: reciben `state`, hacen algo, y **devuelven un diccionario chico con solo los campos que modificaron**. LangGraph fusiona esa devolución en la ficha compartida, sobrescribiendo esos campos. Los nodos no manejan la ficha entera, solo aportan su pedacito.

Ejemplo, el nodo de seguridad (`nodo_sanitizar_entrada`):

def nodo\_sanitizar\_entrada(state: EstadoConsulta):

    pregunta\_limpia \= state\["pregunta"\].strip()\[:MAX\_LARGO\_PREGUNTA\]

    for patron in PATRONES\_SOSPECHOSOS:

        if re.search(patron, pregunta\_limpia.lower()):

            return {

                "pregunta": pregunta\_limpia,

                "pregunta\_original": pregunta\_limpia,

                "respuesta": "Tu consulta no pudo ser procesada por motivos de seguridad...",

                "resuelto": True,

                "motivo\_parada": "bloqueo\_seguridad",

            }

    return {"pregunta": pregunta\_limpia, "pregunta\_original": pregunta\_limpia}

Detalles: `state["pregunta"]` **lee** un campo. `.strip()` saca espacios; `[:MAX_LARGO_PREGUNTA]` recorta el largo (defensa básica: nadie hace una consulta legítima de 5000 caracteres). `re.search` **pregunta** si un patrón aparece (distinto de `re.sub`, que reemplaza). Cuando un `return` se ejecuta, la función **termina ahí**.

**Principio de diseño central:** el nodo **detecta y marca** (deja banderas en la ficha), pero **no decide a dónde ir**. Eso es trabajo de las flechas condicionales. Los nodos hacen el trabajo; las flechas deciden el flujo. Separar esas dos cosas es lo que mantiene el grafo limpio.

## Salida estructurada con Pydantic

Problema: si al LLM se le pregunta "¿esto es urgente?" en lenguaje libre, contesta un párrafo del que hay que adivinar el sí/no. Frágil. La solución profesional es **structured output**: forzar al LLM a responder en un molde exacto y parseable.

from pydantic import BaseModel, Field

class VeredictoTriage(BaseModel):

    es\_urgencia: bool \= Field(description="True si describe una urgencia clinica...")

    motivo: str \= Field(description="Explicacion breve de por que se clasifico asi.")

Conceptos: **Pydantic** define moldes de datos con validación (como `TypedDict` pero más potente). La **`description`** de cada `Field` no es un comentario: LangChain se la pasa al LLM como instrucción, así que se documenta e instruye al mismo tiempo. La línea mágica es **`llm.with_structured_output(VeredictoTriage)`**: envuelve el LLM para que devuelva un objeto que cumple el molde, en vez de texto libre. Después se lee `veredicto.es_urgencia` (un `bool` de verdad) sin adivinar nada.

Se usa en dos nodos: el **triage** (clasificar urgencia) y el **juez** (dar un puntaje de confianza numérico).

## El replanteo del diseño clínico

Esta fue la mejora de diseño más importante, y salió de cuestionar el molde heredado de tickets.

**Por qué "escalar a un humano" no encajaba.** En tickets, escalar era pasar el problema de un agente automático a un operador humano. Pero en el asistente clínico, el que consulta **ya es** el profesional experto. Pasarle el problema "a un humano" cuando el humano es él no tiene sentido.

**La pregunta correcta no es "¿a quién le paso esto?", sino "¿cuándo el sistema NO debería responder como si supiera?".** Y ahí sí hay motivos reales:

- El dato no está en los protocolos (fuera de corpus) → no inventar.  
- El juez da confianza baja → no presentar una respuesta endeble como firme.  
- La pregunta está fuera de alcance → declinar con honestidad.

**Decisión 1: `escalar_humano` se reemplazó por `responder_con_reserva` (abstención honesta).** El peligro número uno de un RAG clínico no es no saber algo: es **contestar con seguridad algo que no está en los protocolos** (alucinación con tono confiado). Para un profesional apurado, una respuesta inventada pero segura es más peligrosa que un "no sé". El comportamiento valioso es **saber callarse**: cuando la confianza no alcanza, en vez de arriesgar, el sistema dice "los protocolos no cubren esto con certeza; verificá en la guía oficial o consultá con el especialista".

**Decisión 2: la urgencia dejó de frenar y pasó a priorizar.** Si un médico pregunta por una crisis hipertensiva, lo peor es frenar y bloquear: el médico quiere el protocolo de emergencia **rápido**. Así que el triage ya no bifurca a un escalamiento: marca `es_urgencia`, deja pasar el flujo hacia el RAG, y el efecto del flag es **anteponer un aviso de prioridad** a la respuesta. La urgencia pasó de freno a acelerador.

**Nota de criterio:** aunque el usuario sea un profesional (que oficia de filtro humano), el triage se calibra hacia "ante la duda, marcá urgencia" — el criterio de no tener falsos negativos sigue siendo la brújula. Y el "humano en el loop" de la célula híbrida vuelve a tener sentido pleno en la Fase 4, cuando el sistema deje de solo *leer* protocolos y empiece a *tocar* la base de pacientes: ahí un gate de aprobación antes de una acción sensible es legítimo.

## El ensamblado del grafo

Los nodos sueltos se convierten en una máquina conectándolos con flechas. Primero, la **función de decisión** (no es un nodo: solo mira la ficha y devuelve una etiqueta de texto):

def decidir\_despues\_de\_evaluar(state: EstadoConsulta):

    if state\["confianza"\] \>= UMBRAL\_CONFIANZA:

        return "responder"

    if state\["intentos"\] \>= MAX\_INTENTOS:

        return "abstenerse"

    return "reintentar"

El orden es una lógica de prioridades: primero chequea lo bueno (¿alcanza?), después lo límite (¿me quedé sin intentos?), y recién reintenta.

El cableado:

from langgraph.graph import StateGraph, START, END

builder \= StateGraph(EstadoConsulta)

builder.add\_node("sanitizar", nodo\_sanitizar\_entrada)

\# ... (los 7 nodos)

builder.add\_edge(START, "sanitizar")

builder.add\_edge("sanitizar", "triage")

builder.add\_edge("triage", "recuperar")

builder.add\_edge("recuperar", "generar")

builder.add\_edge("generar", "evaluar")

builder.add\_conditional\_edges(

    "evaluar",

    decidir\_despues\_de\_evaluar,

    {"responder": "registrar", "reintentar": "refinar", "abstenerse": "reserva"},

)

builder.add\_edge("refinar", "recuperar")   \# EL CICLO: refinar vuelve a buscar

builder.add\_edge("reserva", "registrar")

builder.add\_edge("registrar", END)

Conceptos: `StateGraph(EstadoConsulta)` crea el constructor diciéndole con qué ficha trabaja. `add_node("nombre", funcion)` registra cada nodo con un nombre. `add_edge("desde", "hacia")` tiende una vía fija. `START` y `END` son nodos especiales (entrada y salida). `add_conditional_edges(...)` es la bifurcación: recibe el nodo de origen, la función que decide, y un **diccionario que traduce cada etiqueta a un destino**. Y `add_edge("refinar", "recuperar")` es **la flecha que crea el ciclo**: refinar no va hacia adelante, vuelve a buscar — el ReAct girando.

No se cablea nada especial para la urgencia: el triage marca el flag y deja pasar; el efecto (el aviso) ya vive dentro del nodo `generar`.

## Compilar con memoria: checkpointer y thread\_id

El `builder` es el plano; compilar lo convierte en máquina ejecutable.

from langgraph.checkpoint.memory import InMemorySaver

memoria \= InMemorySaver()

grafo \= builder.compile(checkpointer=memoria)

El **checkpointer** es la memoria: una libreta donde el grafo anota el estado de cada consulta, para poder retomar una conversación donde quedó (puente con la memoria de corto plazo de Agentes). `InMemorySaver` guarda en RAM: dura mientras el programa corre; en producción se cambia por uno en disco/base (una línea).

Al ejecutar, se pasa una config con un **`thread_id`**:

config \= {"configurable": {"thread\_id": "sesion-001"}}

resultado \= grafo.invoke(entrada, config=config)

El `thread_id` es el **identificador de la conversación** (el número de expediente). Todas las consultas con el mismo `thread_id` comparten la misma libreta: el grafo las entiende como la misma conversación. Un `thread_id` distinto es una conversación nueva. Checkpointer y `thread_id` van de la mano: uno es la libreta, el otro es qué página usar.

La entrada solo necesita los campos mínimos (`consulta_id`, `pregunta`, `intentos: 0`); el resto de la ficha se completa sola al pasar por los nodos.

## El problema de rutas e imports

Al correr el grafo apareció `ModuleNotFoundError: No module named 'grafo'`. No era un archivo faltante: era Python buscándolo en el lugar equivocado.

**La lógica:** al correr con `python -m agente.probar_grafo` desde la raíz, el "punto de partida" de Python es la **raíz del proyecto**. Los imports son relativos a ese punto de partida, **no** a la carpeta donde está el archivo. Por eso `from grafo import grafo` fallaba: desde la raíz, `grafo` no es visible directo.

**La solución:** todos los imports internos usan la ruta completa desde la raíz (`from agente.grafo import grafo`, `from agente.estado import ...`). Y se crean archivos `__init__.py` vacíos en `agente/` y `retrieval/`: su sola presencia le dice a Python "esta carpeta es un paquete importable". Sin ellos aparecen la mitad de los `ModuleNotFoundError` del mundo.

**La regla mental:** si en un archivo usás un nombre que no definiste ahí, necesitás un import que lo traiga. Y se corre como módulo desde la raíz: `python -m agente.probar_grafo` (con puntos), no `python agente/probar_grafo.py` (con barra).

## La resiliencia: manejar los fallos del LLM

Al probar, apareció un error de producción real: `429 RESOURCE_EXHAUSTED` — se agotó la cuota gratis de Gemini (20 requests/día en el free tier de `gemini-2.5-flash-lite`).

**Aprendizaje de arquitectura:** un sistema agéntico consume cuota mucho más rápido que un chatbot simple. Cada consulta hace **varias** llamadas al LLM (triage \+ generar \+ juez, y si el loop refina, se duplican): 3 a 5 llamadas por consulta. Entre varias pruebas se agotan 20 en una sesión.

**Cómo leer un traceback gigante:** el 90% son tripas de las librerías. Lo único que importa es la última línea con el mensaje real. Acá: `429 ... limit: 20`.

**Dos tipos de rate limit, que se manejan distinto:**

- **Por minuto** (transitorio): esperar y reintentar sí lo resuelve. `ChatGoogleGenerativeAI` ya trae `max_retries=6` que reintenta con backoff (el exponential backoff con jitter de Automation, ya incorporado en la librería).  
- **Por día** (agotado): reintentar no sirve. Lo correcto es **degradar con gracia**: capturar el error y devolver una respuesta controlada en vez de explotar.

**La solución: una centralita única de acceso al LLM** (`agente/llm_seguro.py`). En vez de que cada nodo llame al LLM por su cuenta, todos pasan por una función que envuelve la llamada con manejo de error:

def invocar\_llm(prompt, con\_estructura=None):

    modelo \= llm.with\_structured\_output(con\_estructura) if con\_estructura else llm

    try:

        resultado \= modelo.invoke(prompt)

        return True, resultado

    except Exception as error:

        print(f"\[LLM\] La llamada al modelo fallo: {type(error).\_\_name\_\_}")

        return False, None

Conceptos: **`try/except`** es la red de contención de Python — "intentá esto (`try`); si se rompe, hacé esto otro (`except`) en vez de morir". El trapecista con red. El patrón de la **tupla `(exito, resultado)`** es elegante: la función devuelve dos cosas — primero un `bool` que dice "¿salió bien?", después el resultado (o `None`). Un semáforo pegado al paquete: el que recibe mira el semáforo antes de abrir la caja. Eso obliga a cada nodo a manejar el error explícitamente.

**La degradación coherente con el rol clínico de cada nodo:** cada nodo, tras `exito, resultado = invocar_llm(...)`, chequea el semáforo (`if not exito:`) y toma un camino seguro. El triage peca de precavido (marca urgencia). El generar deja respuesta vacía → el juez la puntúa 0 → abstención. El evaluar, si no puede juzgar, asume confianza 0 → abstención. El refinar deja la pregunta como estaba. **Ningún nodo asume que el LLM siempre responde.**

El resultado global: donde antes el sistema **explotaba** con un traceback ante el `429`, ahora **degrada hasta una abstención honesta**. Ese es el cambio de "código que anda en mi máquina" a "código que aguanta en producción".

## El diagrama del grafo final

                         START

                           |

                           v

                 ┌──────────────────┐

                 │ sanitizar\_entrada │  seguridad (limpieza \+ inyeccion)

                 └─────────┬─────────┘

                           v

                 ┌──────────────────┐

                 │ triage\_urgencia   │  marca es\_urgencia (NO frena)

                 └─────────┬─────────┘

                           v

                 ┌──────────────────┐

              ┌─►│    recuperar      │  RAG real (Fase 2): buscar\_protocolos()

              │  └─────────┬─────────┘

              │            v

              │  ┌──────────────────┐

              │  │     generar       │  si es\_urgencia \-\> antepone aviso

              │  └─────────┬─────────┘

              │            v

              │  ┌──────────────────┐

              │  │     evaluar       │  juez (LLM-as-judge) \-\> confianza

              │  └─────────┬─────────┘

              │       ¿alcanza?

              │   ┌────────┼───────────────┐

              │ responder reintentar   abstenerse

              │   │         │               │

              │   │    ┌─────────┐          │

              │   │    │ refinar │          │

              │   │    └────┬────┘          │

              │   │         └───────────────┼──► (vuelve a recuperar)

              │   │                          v

              │   │              ┌──────────────────┐

              │   │              │ responder\_con\_    │  abstencion honesta

              │   │              │    reserva        │

              │   │              └─────────┬────────┘

              │   v                        v

              │  ┌────────────────────────────┐

              └──┤    registrar\_resultado      │  idempotente

                 └──────────────┬─────────────┘

                                v

                               END

## Consideraciones de producción

- **El costo de un sistema agéntico.** Cada consulta dispara varias llamadas al LLM (3-5), no una. En producción esto se mide (costo por consulta) y se optimiza. Es la razón por la que la cuota se agota rápido, y un punto central de la Fase 5 (métricas de costo).  
- **Resiliencia ante servicios externos.** El sistema no puede caerse cuando una API dice "basta". Se maneja en dos capas: `max_retries` de la librería (para límites transitorios) \+ degradación con gracia en la centralita (para fallos persistentes).  
- **Los mensajes críticos se hardcodean, no se generan.** El aviso de urgencia y el mensaje de abstención son textos fijos (constantes), no generados por el LLM. Garantiza que una alerta crítica sea siempre idéntica y siempre esté.  
- **La memoria en producción.** `InMemorySaver` se borra al reiniciar. Para persistencia real (sobrevivir reinicios) se cambia por un checkpointer en disco/base — tema de la Fase 3 de persistencia / Práctica \#5.  
- **El triage por LLM no es infalible.** Se calibra conservador (ante la duda, urgencia) y el sistema es de *apoyo*, nunca reemplazo. En producción se evaluaría con muchos casos reales, midiendo sobre todo los falsos negativos.  
- **Imprecisión del corpus detectada:** ante 220/130 con síntomas, la respuesta sugirió "manejo ambulatorio", sin distinguir bien urgencia vs. emergencia hipertensiva. Es una limitación del chunk recuperado, a revisar al pulir el corpus. Refuerza que el profesional tiene la última palabra.

## Glosario de esta fase

- **Grafo de estado (StateGraph):** estructura de nodos y flechas por la que fluye un estado compartido, con decisiones y ciclos.  
- **Nodo:** una función que recibe el estado, hace un trabajo y devuelve los campos que modificó.  
- **Flecha (edge):** conexión fija entre dos nodos.  
- **Flecha condicional:** bifurcación; una función mira el estado y decide el destino.  
- **Ciclo:** una flecha que vuelve a un nodo anterior, para iterar (con tope: `MAX_INTENTOS`).  
- **Checkpointer:** el componente que persiste el estado (la memoria del grafo).  
- **thread\_id:** identificador de una conversación; agrupa consultas en la misma memoria.  
- **TypedDict:** diccionario con forma fija y tipada; se usa para el Estado.  
- **Pydantic / BaseModel:** librería para definir moldes de datos con validación; se usa para la salida estructurada.  
- **Structured output:** forzar al LLM a responder en un molde exacto y parseable, no en prosa libre.  
- **LLM como juez (LLM-as-a-judge):** usar un segundo LLM para evaluar la respuesta del primero.  
- **Faithfulness:** qué tan fiel es una respuesta a su fuente (lo que el juez mide sobre todo).  
- **Abstención honesta:** que el sistema, ante baja confianza, diga "no sé con certeza" en vez de arriesgar.  
- **Idempotencia:** que ejecutar algo una o varias veces dé el mismo resultado (el registro pasa una sola vez).  
- **try/except:** mecanismo de Python para capturar errores sin que el programa explote.  
- **Degradación con gracia (graceful degradation):** ante un fallo, dar una respuesta controlada en vez de caerse.  
- **Exponential backoff:** reintentar esperando cada vez más tiempo; con *jitter* se le suma azar para no saturar.  
- **Rate limit (429):** límite de uso de una API; puede ser por minuto (transitorio) o por día (agotado).  
- **`__init__.py`:** archivo (a menudo vacío) que marca una carpeta como paquete importable de Python.

## Estado del proyecto

**Completado hasta este checkpoint:**

- **Fase 1 — Setup.** ✅ (ver `fase_1_y_2.md`)  
- **Fase 2 — RAG.** ✅ (ver `fase_1_y_2.md`)  
- **Fase 3 — Agente cíclico.** ✅ Grafo LangGraph completo: 7 nodos (seguridad, triage de urgencia, recuperación conectada al RAG, generación con aviso de urgencia, evaluación por juez, abstención honesta, registro idempotente), bifurcación con lógica de decisión, ciclo de refinamiento con tope, memoria vía checkpointer, y centralita resiliente (`llm_seguro`) con degradación con gracia.

**Pendiente de probar (cuando se renueve la cuota de Gemini):** el caso de abstención honesta (pregunta fuera de corpus) y el comportamiento resiliente ante el rate limit.

**Archivos de código de esta fase:** `agente/estado.py`, `agente/grafo.py`, `agente/llm_seguro.py`, `agente/probar_grafo.py`, más los `__init__.py` de `agente/` y `retrieval/`. Ver `mapa_de_archivos.md` para el detalle de qué hace cada uno.

**Próximo paso — Fase 4 (conexión segura y MCP):** conectar el sistema a la base de pacientes (SQL de solo lectura) mediante un adaptador seguro (validar, autorizar, ejecutar, sanitizar PII, auditar), y construir un servidor MCP. Aquí vuelve el "humano en el loop" con sentido pleno: un gate de aprobación antes de tocar datos sensibles.  
