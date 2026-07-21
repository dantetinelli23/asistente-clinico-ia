# agente/estado.py
# Define el ESTADO del grafo: la "ficha" que viaja por todos los nodos.
# Cada nodo la recibe, lee lo que necesita, y devuelve los campos que modifico.

from typing import TypedDict, List


class EstadoConsulta(TypedDict):
    # --- Identificacion ---
    consulta_id: str          # identificador unico de esta consulta (para logs y persistencia)

    # --- La pregunta ---
    pregunta: str             # la pregunta actual (puede reformularse en el loop)
    pregunta_original: str    # la pregunta tal como la escribio el profesional (nunca cambia)

    # --- Recuperacion y generacion ---
    documentos: List[str]     # los chunks recuperados por el RAG
    respuesta: str            # la respuesta generada por el LLM

    # --- Control del ciclo ---
    intentos: int             # cuantas veces se intento responder (tope para no girar infinito)
    confianza: float          # puntaje 0-1 que el juez le da a la respuesta

    # --- Seguridad clinica ---
    es_urgencia: bool         # True si el triage detecto una urgencia -> escalar a humano

    # --- Estado final ---
    escalado: bool            # True si se derivo a un humano
    resuelto: bool            # True si el flujo termino (por respuesta o por escalamiento)
    registrado: bool          # True si ya se registro el resultado (idempotencia)
    motivo_parada: str        # por que se detuvo: "confianza suficiente", "urgencia", etc.