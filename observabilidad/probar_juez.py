# observabilidad/probar_juez.py
# Prueba el nodo evaluar (el juez) contra un golden set de casos trampa,
# sin correr el grafo completo. Cada caso llama al juez UNA sola vez.

from dotenv import load_dotenv
load_dotenv()

from agente.grafo import nodo_evaluar_respuesta

casos = [

    {
        "id": "control_hidroclorotiazida_atribucion_correcta",
        "pregunta_original": "¿Se recomienda la dosis alta de Hidroclorotiazida?",
        "documentos": [
            "Tiazidas (TZ-STZ). Fármacos, Dosis baja, Dosis media, Dosis alta. "
            "Clortalidona: 6,25 mg/día, 12,5 mg/día, 25 mg/día. "
            "Hidroclorotiazida: 12,5 mg/día, 25 mg/día, 50 mg/día**. "
            "Indapamida: 1,25 mg/día, 2,5 mg/día, ---. "
            "** dosis no recomendada, por elevada tasa de efectos adversos."
        ],
        "respuesta": (
            "La dosis alta de Hidroclorotiazida (50 mg/día) no se recomienda "
            "por su elevada tasa de efectos adversos."
        ),
        "veredicto_esperado": "alta",
    },
]

print("=" * 70)
print("GOLDEN SET - EVALUACION DEL JUEZ")
print("=" * 70)

for caso in casos:
    state_de_prueba = {
        "intentos": 0,
        "documentos": caso["documentos"],
        "respuesta": caso["respuesta"],
        "pregunta_original": caso["pregunta_original"],
    }

    resultado = nodo_evaluar_respuesta(state_de_prueba)
    confianza = resultado["confianza"]

    if caso["veredicto_esperado"] == "alta":
        acierto = confianza >= 0.7
    else:
        acierto = confianza < 0.7

    marca = "OK" if acierto else "FALLO DEL JUEZ"
    if resultado.get("motivo_parada") == "evaluador_no_disponible":
        print("  (ADVERTENCIA: el LLM fallo por infraestructura, no es un veredicto real del juez)")

    print(f"\nCaso: {caso['id']}")
    print(f"  Esperado: {caso['veredicto_esperado']} | Confianza real: {confianza}")
    print(f"  -> {marca}")