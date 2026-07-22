# observabilidad/resumen_metricas.py
# Le pregunta a LangSmith por todas las corridas del proyecto y calcula
# metricas agregadas: latencia, costo, tokens y tasa de abstencion.

from dotenv import load_dotenv
load_dotenv()

from langsmith import Client

cliente = Client()
NOMBRE_PROYECTO = "asistente-clinico"

corridas = list(cliente.list_runs(
    project_name=NOMBRE_PROYECTO,
    is_root=True,
    filter='eq(name, "LangGraph")',
))

print(f"Corridas encontradas: {len(corridas)}")


datos = []

for corrida in corridas:
    tuvo_error = corrida.error is not None

    if corrida.start_time and corrida.end_time:
        latencia = (corrida.end_time - corrida.start_time).total_seconds()
    else:
        latencia = None

    salida = corrida.outputs or {}
    motivo_parada = salida.get("motivo_parada")
    confianza = salida.get("confianza")

    datos.append({
        "consulta_id": (corrida.inputs or {}).get("consulta_id", "desconocido"),
        "tuvo_error": tuvo_error,
        "latencia_seg": latencia,
        "tokens": corrida.total_tokens,
        "costo_usd": corrida.total_cost,
        "motivo_parada": motivo_parada,
        "confianza": confianza,
    })

for d in datos:
    print(d)

exitosas = [d for d in datos if not d["tuvo_error"]]
fallidas = [d for d in datos if d["tuvo_error"]]

total_corridas = len(datos)
tasa_error = len(fallidas) / total_corridas


latencias = sorted(d["latencia_seg"] for d in exitosas if d["latencia_seg"] is not None)
costos = [float(d["costo_usd"]) for d in exitosas if d["costo_usd"] is not None]
tokens = [d["tokens"] for d in exitosas if d["tokens"] is not None]

def percentil(lista_ordenada, p):
    if not lista_ordenada:
        return None
    indice = int(round((p / 100) * (len(lista_ordenada) - 1)))
    return lista_ordenada[indice]

abstenciones = [d for d in exitosas if d["motivo_parada"] == "confianza_insuficiente"]
tasa_abstencion = len(abstenciones) / len(exitosas) if exitosas else 0

print("\n" + "=" * 60)
print("RESUMEN DE METRICAS - asistente-clinico")
print("=" * 60)
print(f"Corridas totales:       {total_corridas}")
print(f"Corridas exitosas:      {len(exitosas)}")
print(f"Corridas con error:     {len(fallidas)} (tasa de error: {tasa_error:.0%})")
print(f"Tasa de abstencion:     {tasa_abstencion:.0%} ({len(abstenciones)} de {len(exitosas)} exitosas)")
print(f"Latencia P50:           {percentil(latencias, 50):.2f}s")
print(f"Latencia P95:           {percentil(latencias, 95):.2f}s")
print(f"Costo total (exitosas): ${sum(costos):.6f}")
print(f"Costo promedio:         ${(sum(costos) / len(costos)):.6f}")
print(f"Tokens promedio:        {sum(tokens) / len(tokens):.0f}")