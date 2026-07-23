# api.py
# El servidor web que expone el sistema como un servicio.
# Se corre con: uvicorn api:app --reload

import uuid
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agente.grafo import grafo

app = FastAPI()


# --- El "molde" de lo que debe traer el pedido ---
class PreguntaEntrada(BaseModel):
    pregunta: str


@app.post("/consulta")
async def hacer_consulta(entrada: PreguntaEntrada):
    consulta_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": consulta_id}}

    estado_inicial = {
        "consulta_id": consulta_id,
        "pregunta": entrada.pregunta,
        "intentos": 0,
    }

    try:
        resultado = await grafo.ainvoke(estado_inicial, config=config)
    except Exception as error:
        print(f"[API] Error inesperado en consulta {consulta_id}: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=503,
            detail="El servicio no pudo procesar la consulta en este momento. Intentá nuevamente en unos minutos.",
        )

    return {
        "consulta_id": consulta_id,
        "respuesta": resultado["respuesta"],
        "confianza": resultado.get("confianza"),
        "urgencia": resultado.get("es_urgencia", False),
        "motivo_parada": resultado.get("motivo_parada"),
    }


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")