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
        return False, None# agente/llm_seguro.py
# Centralita unica para hablar con el LLM. Todos los nodos pasan por aca.
# Si el proveedor principal falla, se prueba un proveedor de respaldo
# (fallback de proveedor, capa 2 de resiliencia). Si los dos fallan,
# degradamos con gracia en vez de dejar que el sistema explote.

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

# Proveedor principal: Gemini. max_retries=6 (por defecto) ya reintenta
# con backoff los errores transitorios (rate limit por minuto).
llm_principal = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)

# Proveedor de respaldo: Groq, solo se llama si el principal fallo del todo
# (por ejemplo, rate limit por dia, que no se arregla reintentando).
llm_respaldo = ChatGroq(model="openai/gpt-oss-120b", temperature=0)


def invocar_llm(prompt, con_estructura=None):
    """Punto unico de acceso al LLM.
    - prompt: el texto (o mensajes) a enviar.
    - con_estructura: si se pasa un modelo Pydantic, devuelve salida estructurada.
    Devuelve una tupla (exito, resultado):
    - (True, respuesta)  si algun proveedor contesto bien.
    - (False, None)      si los dos proveedores fallaron.
    """
    modelo_principal = llm_principal.with_structured_output(con_estructura) if con_estructura else llm_principal
    modelo_respaldo = llm_respaldo.with_structured_output(con_estructura) if con_estructura else llm_respaldo

    try:
        resultado = modelo_principal.invoke(prompt)
        return True, resultado
    except Exception as error_principal:
        print(f"[LLM] Gemini (principal) fallo: {type(error_principal).__name__}. Probando Groq (respaldo)...")
        try:
            resultado = modelo_respaldo.invoke(prompt)
            return True, resultado
        except Exception as error_respaldo:
            print(f"[LLM] Groq (respaldo) tambien fallo: {type(error_respaldo).__name__}")
            return False, None