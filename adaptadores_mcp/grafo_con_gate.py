from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

from adaptadores_mcp.adaptador_seguro import consultar_paciente


class EstadoAcceso(TypedDict):
    usuario: str
    patient_id: int
    decision: str
    ficha: dict


def gate_humano(state: EstadoAcceso):
    """Frena y le pide aprobación al profesional antes de tocar la ficha."""
    respuesta = interrupt({
        "aviso": "Se va a acceder a la ficha de un paciente. ¿Autorizás?",
        "usuario": state["usuario"],
        "patient_id": state["patient_id"],
    })
    return {"decision": respuesta}


def consultar(state: EstadoAcceso):
    """Solo corre si hubo aprobación. Acá SÍ ocurre el acceso real."""
    ficha = consultar_paciente(state["usuario"], state["patient_id"])
    return {"ficha": ficha}


def cancelado(state: EstadoAcceso):
    """El profesional no aprobó: no se toca nada."""
    return {"ficha": {"estado": "acceso cancelado por el profesional"}}


def decidir(state: EstadoAcceso):
    return "consultar" if state["decision"] == "aprobar" else "cancelado"


builder = StateGraph(EstadoAcceso)
builder.add_node("gate_humano", gate_humano)
builder.add_node("consultar", consultar)
builder.add_node("cancelado", cancelado)

builder.add_edge(START, "gate_humano")
builder.add_conditional_edges("gate_humano", decidir, {
    "consultar": "consultar",
    "cancelado": "cancelado",
})
builder.add_edge("consultar", END)
builder.add_edge("cancelado", END)

grafo = builder.compile(checkpointer=InMemorySaver())


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "consulta-001"}}
    entrada = {"usuario": "dr_gomez", "patient_id": 1}

    # 1) Corremos hasta que el grafo se frena en el gate
    resultado = grafo.invoke(entrada, config)
    print("El grafo se frenó y está pidiendo aprobación:")
    print(resultado["__interrupt__"])

    # 2) El humano decide. Probá cambiando "aprobar" por "rechazar".
    decision_humana = "rechazar"

    # 3) Retomamos el grafo con la decisión
    final = grafo.invoke(Command(resume=decision_humana), config)
    print("\nResultado final:")
    print(final["ficha"])