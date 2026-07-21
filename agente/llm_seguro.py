# agente/llm_seguro.py
# Centralita unica para hablar con el LLM. Todos los nodos pasan por aca.
# Si el LLM falla (rate limit, red, etc.), degradamos con gracia en vez
# de dejar que el sistema explote.

from langchain_google_genai import ChatGoogleGenerativeAI

# El modelo. max_retries=6 (por defecto) ya reintenta con backoff los
# errores transitorios; nosotros manejamos el caso en que aun asi falle.
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)


def invocar_llm(prompt, con_estructura=None):
    """Punto unico de acceso al LLM.
    - prompt: el texto (o mensajes) a enviar.
    - con_estructura: si se pasa un modelo Pydantic, devuelve salida estructurada.
    Devuelve una tupla (exito, resultado):
    - (True, respuesta)  si el LLM contesto bien.
    - (False, None)      si el LLM fallo tras agotar los reintentos.
    """
    modelo = llm.with_structured_output(con_estructura) if con_estructura else llm

    try:
        resultado = modelo.invoke(prompt)
        return True, resultado
    except Exception as error:
        # Degradacion con gracia: no explotamos, avisamos que fallo.
        print(f"[LLM] La llamada al modelo fallo: {type(error).__name__}")
        return False, None