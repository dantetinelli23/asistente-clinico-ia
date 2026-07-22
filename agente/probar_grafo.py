# agente/probar_grafo.py
# Ejecuta el grafo con una pregunta de prueba, para verlo funcionar entero.

from agente.grafo import grafo

# --- La consulta de entrada ---
# Damos SOLO los campos que el grafo necesita para arrancar; el resto
# de la ficha se va completando sola a medida que pasa por los nodos.
entrada = {
    "consulta_id": "caso2-diabetes-repeticion-3",
    "pregunta": "¿cuál es el tratamiento para la diabetes tipo 1?",
    "intentos": 0,
}

# --- La configuracion de la sesion (para la memoria) ---
config = {"configurable": {"thread_id": "sesion-caso2-rep3"}}

# --- Ejecutar el grafo ---
resultado = grafo.invoke(entrada, config=config)

# --- Mostrar el resultado final ---
print("\n" + "=" * 60)
print("RESPUESTA FINAL:")
print("=" * 60)
print(resultado["respuesta"])
print("\n--- Datos del proceso ---")
print(f"Urgencia:  {resultado.get('es_urgencia')}")
print(f"Intentos:  {resultado.get('intentos')}")
print(f"Confianza: {resultado.get('confianza')}")
print(f"Motivo:    {resultado.get('motivo_parada')}")