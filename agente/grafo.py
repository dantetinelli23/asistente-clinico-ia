# agente/grafo.py
# Construye el grafo ciclico del asistente clinico (LangGraph).
# Se arma por partes: primero los nodos, al final el ensamblado.

from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from retrieval.buscador import buscar_protocolos
import re
from estado import EstadoConsulta

# --- CONSTANTES DE SEGURIDAD ---
MAX_LARGO_PREGUNTA = 500   # recortamos preguntas absurdamente largas

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
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)


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
    # Si el nodo anterior ya freno por seguridad, no hacemos nada.
    if state.get("resuelto"):
        return {}

    clasificador = llm.with_structured_output(VeredictoTriage)

    prompt_triage = f"""Sos un sistema de triage clinico. Analiza la siguiente consulta
de un profesional de salud y determina si describe una URGENCIA o EMERGENCIA clinica
que requiere atencion humana inmediata (por ejemplo: valores criticos con sintomas,
signos de riesgo vital, deterioro agudo), o si es una consulta informativa de rutina
(por ejemplo: preguntar un umbral, una dosis, un criterio diagnostico).

CONSULTA:
{state["pregunta"]}"""

    veredicto = clasificador.invoke(prompt_triage)

    if veredicto.es_urgencia:
        return {
            "es_urgencia": True,
            "motivo_parada": f"urgencia: {veredicto.motivo}",
        }

    return {"es_urgencia": False}