# agente/grafo.py
# Construye el grafo ciclico del asistente clinico (LangGraph).
# Se arma por partes: primero los nodos, al final el ensamblado.

from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from retrieval.buscador import buscar_protocolos
import re
from agente.estado import EstadoConsulta
from orquestacion.cadena_generacion import plantilla_generacion, AVISO_URGENCIA
from agente.llm_seguro import invocar_llm


# --- CONSTANTES DE SEGURIDAD ---
MAX_LARGO_PREGUNTA = 500   # recortamos preguntas absurdamente largas
MAX_INTENTOS = 2
UMBRAL_CONFIANZA = 0.7
# Patrones de "inyeccion de prompt": intentos de manipular al asistente
# para que ignore sus instrucciones. Adaptado de tu Practica 10.
PATRONES_SOSPECHOSOS = [
    r"ignor[a-z]* (las |todas las )?instruccion",
    r"olvid[a-z]* (tu|las) instruccion",
    r"actua como",
    r"system prompt",
]


# --- NODO 1: sanitizar la entrada (seguridad) ---
def nodo_sanitizar_entrada(state: EstadoConsulta):
    # 1. Limpieza basica: sacar espacios sobrantes y recortar el largo.
    pregunta_limpia = state["pregunta"].strip()[:MAX_LARGO_PREGUNTA]

    # 2. Deteccion de inyeccion de prompt.
    for patron in PATRONES_SOSPECHOSOS:
        if re.search(patron, pregunta_limpia.lower()):
            return {
                "pregunta": pregunta_limpia,
                "pregunta_original": pregunta_limpia,
                "respuesta": "Tu consulta no pudo ser procesada por motivos de seguridad. Reformulala y volve a intentar.",
                "resuelto": True,
                "motivo_parada": "bloqueo_seguridad",
            }

    # 3. Si paso los controles, dejamos la pregunta limpia y guardamos el original.
    return {
        "pregunta": pregunta_limpia,
        "pregunta_original": pregunta_limpia,
    }

# --- MODELO DE LENGUAJE ---


# --- MOLDE DE SALIDA ESTRUCTURADA PARA EL TRIAGE ---
class VeredictoTriage(BaseModel):
    es_urgencia: bool = Field(
        description="True si la consulta describe una urgencia o emergencia clinica "
                    "que requiere atencion humana inmediata; False si es una consulta "
                    "informativa de rutina."
    )
    motivo: str = Field(
        description="Explicacion breve (una frase) de por que se clasifico asi."
    )


# --- NODO 2: triage de urgencia (usa el LLM como clasificador) ---
def nodo_triage_urgencia(state: EstadoConsulta):
    if state.get("resuelto"):
        return {}

    prompt_triage = f"""Sos un sistema de triage clinico. Analiza la siguiente consulta
de un profesional de salud y determina si describe una URGENCIA o EMERGENCIA clinica
que requiere atencion humana inmediata (por ejemplo: valores criticos con sintomas,
signos de riesgo vital, deterioro agudo), o si es una consulta informativa de rutina
(por ejemplo: preguntar un umbral, una dosis, un criterio diagnostico).

CONSULTA:
{state["pregunta"]}"""

    exito, veredicto = invocar_llm(prompt_triage, con_estructura=VeredictoTriage)

    # Si el LLM fallo, degradamos SEGURO: ante la duda, marcamos urgencia.
    if not exito:
        return {"es_urgencia": True, "motivo_parada": "triage_no_disponible"}

    if veredicto.es_urgencia:
        return {"es_urgencia": True, "motivo_parada": f"urgencia: {veredicto.motivo}"}
    return {"es_urgencia": False}

# --- NODO 3: recuperar (conecta con el RAG de la Fase 2) ---
def nodo_recuperar(state: EstadoConsulta):
    documentos = buscar_protocolos(state["pregunta"])
    return {"documentos": documentos}


# --- NODO 4: generar la respuesta ---
def nodo_generar_respuesta(state: EstadoConsulta):
    if not state["documentos"]:
        return {"respuesta": ""}

    contexto = "\n\n".join(state["documentos"])

    prompt_armado = plantilla_generacion.invoke({
        "contexto": contexto,
        "pregunta": state["pregunta_original"],
    })
    exito, resultado = invocar_llm(prompt_armado)

    # Si el LLM fallo, respuesta vacia -> el juez dara confianza 0 -> abstencion.
    if not exito:
        return {"respuesta": ""}

    respuesta = resultado.content.strip()

    if state.get("es_urgencia"):
        respuesta = AVISO_URGENCIA + respuesta

    return {"respuesta": respuesta}

# --- MOLDE DE SALIDA DEL JUEZ (structured output) ---
class VeredictoEvaluacion(BaseModel):
    confianza: float = Field(
        description="Puntaje de 0.0 a 1.0 sobre que tan bien la RESPUESTA "
                    "resuelve la PREGUNTA usando SOLO el CONTEXTO. "
                    "1.0 = completa y fiel al contexto; 0.5 = parcial; "
                    "0.0 = no la resuelve o no se apoya en el contexto."
    )


# --- NODO 5: evaluar la respuesta (LLM como juez) ---
def nodo_evaluar_respuesta(state: EstadoConsulta):
    intentos_nuevos = state["intentos"] + 1

    if not state["documentos"] or not state["respuesta"]:
        return {
            "intentos": intentos_nuevos,
            "confianza": 0.0,
            "motivo_parada": "sin_informacion",
        }

    contexto = "\n\n".join(state["documentos"])

    prompt_juez = f"""Sos un evaluador de calidad de respuestas clinicas.
Evalua que tan bien la RESPUESTA contesta la PREGUNTA, usando UNICAMENTE
la informacion del CONTEXTO. Penaliza fuerte si la respuesta afirma algo
que no esta en el contexto (alucinacion).

PREGUNTA:
{state["pregunta_original"]}

CONTEXTO:
{contexto}

RESPUESTA A EVALUAR:
{state["respuesta"]}"""

    exito, veredicto = invocar_llm(prompt_juez, con_estructura=VeredictoEvaluacion)

    # Si el juez no pudo evaluar, confianza 0 -> el sistema se abstiene.
    if not exito:
        return {
            "intentos": intentos_nuevos,
            "confianza": 0.0,
            "motivo_parada": "evaluador_no_disponible",
        }

    confianza = max(0.0, min(1.0, veredicto.confianza))
    return {"intentos": intentos_nuevos, "confianza": confianza}

# --- NODO 6: responder con reserva (abstencion honesta) ---
# Se activa cuando la confianza quedo baja o no habia informacion:
# en vez de arriesgar una respuesta inventada, el sistema se abstiene.
def nodo_responder_con_reserva(state: EstadoConsulta):
    mensaje_reserva = (
        "Los protocolos disponibles no cubren esta consulta con certeza "
        "suficiente. Se recomienda verificar en la guia clinica oficial "
        "completa o consultar con el especialista de referencia."
    )
    return {
        "respuesta": mensaje_reserva,
        "motivo_parada": "confianza_insuficiente",
        "resuelto": True,
    }


# --- NODO 7: registrar el resultado (idempotente) ---
def nodo_registrar_resultado(state: EstadoConsulta):
    # Idempotencia: si ya se registro, no lo hacemos de nuevo.
    if state.get("registrado"):
        return {}

    # Por ahora, "registrar" es dejar traza en consola. Mas adelante
    # (Fase 5, observabilidad) esto ira a un sistema real de logs/metricas.
    print("=" * 60)
    print(f"[REGISTRO] consulta_id: {state.get('consulta_id', 'N/A')}")
    print(f"[REGISTRO] pregunta:    {state.get('pregunta_original', '')}")
    print(f"[REGISTRO] urgencia:    {state.get('es_urgencia', False)}")
    print(f"[REGISTRO] confianza:   {state.get('confianza', 0.0)}")
    print(f"[REGISTRO] motivo:      {state.get('motivo_parada', 'N/A')}")
    print("=" * 60)

    return {
        "registrado": True,
        "resuelto": True,
    }

# --- FUNCION DE DECISION (el cerebro de la bifurcacion) ---
# No es un nodo: es la funcion que la flecha condicional usa para decidir
# el camino despues de evaluar. Mira el estado y devuelve un texto-etiqueta.
def decidir_despues_de_evaluar(state: EstadoConsulta):
    if state["confianza"] >= UMBRAL_CONFIANZA:
        return "responder"          # la respuesta es buena -> registrar y terminar
    if state["intentos"] >= MAX_INTENTOS:
        return "abstenerse"         # se agotaron los intentos -> reserva honesta
    return "reintentar"             # todavia puedo mejorar -> refinar y volver a buscar


# --- NODO 8: refinar la consulta (reformula para buscar mejor) ---
def nodo_refinar_consulta(state: EstadoConsulta):
    prompt_refinar = f"""Reformula la siguiente consulta clinica para mejorar
la busqueda en una base de protocolos. Usa sinonimos o terminos mas tecnicos,
sin cambiar el sentido de la pregunta original. Devolve SOLO la consulta
reformulada, sin comillas ni explicaciones.

CONSULTA ORIGINAL:
{state["pregunta_original"]}

VERSION ACTUAL (no dio buenos resultados):
{state["pregunta"]}"""

    exito, resultado = invocar_llm(prompt_refinar)

    # Si falla el refinado, dejamos la pregunta como estaba (no rompe el flujo).
    if not exito:
        return {"pregunta": state["pregunta"]}

    return {"pregunta": resultado.content.strip()}


# --- CONSTRUCCION DEL GRAFO ---
from langgraph.graph import StateGraph, START, END

builder = StateGraph(EstadoConsulta)

# 1. Registrar cada nodo con un nombre.
builder.add_node("sanitizar", nodo_sanitizar_entrada)
builder.add_node("triage", nodo_triage_urgencia)
builder.add_node("recuperar", nodo_recuperar)
builder.add_node("generar", nodo_generar_respuesta)
builder.add_node("evaluar", nodo_evaluar_respuesta)
builder.add_node("refinar", nodo_refinar_consulta)
builder.add_node("reserva", nodo_responder_con_reserva)
builder.add_node("registrar", nodo_registrar_resultado)

# 2. Flechas fijas (el camino principal).
builder.add_edge(START, "sanitizar")
builder.add_edge("sanitizar", "triage")
builder.add_edge("triage", "recuperar")
builder.add_edge("recuperar", "generar")
builder.add_edge("generar", "evaluar")

# 3. Flecha CONDICIONAL: despues de evaluar, se bifurca segun la decision.
builder.add_conditional_edges(
    "evaluar",
    decidir_despues_de_evaluar,
    {
        "responder": "registrar",
        "reintentar": "refinar",
        "abstenerse": "reserva",
    },
)

# 4. Cerrar los caminos.
builder.add_edge("refinar", "recuperar")   # el CICLO: refinar vuelve a buscar
builder.add_edge("reserva", "registrar")
builder.add_edge("registrar", END)


# --- COMPILAR EL GRAFO CON MEMORIA ---
from langgraph.checkpoint.memory import InMemorySaver

memoria = InMemorySaver()
grafo = builder.compile(checkpointer=memoria)