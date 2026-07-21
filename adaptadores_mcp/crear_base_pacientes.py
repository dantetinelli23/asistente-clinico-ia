import sqlite3
from pathlib import Path

RUTA_BASE = Path(__file__).parent / "pacientes.db"

pacientes = [
    (1, "María González",  "28.456.789", "2615551234", 58, "Hipertensión arterial", "Enalapril 10mg",   "150/95"),
    (2, "Jorge Fernández", "20.111.222", "2615559876", 67, "Hipertensión + Diabetes", "Losartán 50mg",  "160/100"),
    (3, "Ana Ruiz",        "35.678.901", "2615554321", 42, "Hipertensión leve",      "Sin medicación",  "138/88"),
]

conexion = sqlite3.connect(RUTA_BASE)
cursor = conexion.cursor()

cursor.execute("DROP TABLE IF EXISTS pacientes")
cursor.execute("""
    CREATE TABLE pacientes (
        id           INTEGER PRIMARY KEY,
        nombre       TEXT,
        dni          TEXT,
        telefono     TEXT,
        edad         INTEGER,
        diagnostico  TEXT,
        medicacion   TEXT,
        presion      TEXT
    )
""")

cursor.executemany(
    "INSERT INTO pacientes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    pacientes
)

conexion.commit()
conexion.close()

print(f"Base creada con {len(pacientes)} pacientes en: {RUTA_BASE}")