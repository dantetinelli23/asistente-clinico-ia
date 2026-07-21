import sqlite3
import re
from pathlib import Path
from datetime import datetime

RUTA_BASE = Path(__file__).parent / "pacientes.db"
RUTA_AUDITORIA = Path(__file__).parent / "auditoria.log"

# Qué profesional puede ver qué. En producción esto vendría de una base de
# permisos real; acá lo dejamos como un diccionario simple para practicar.
PERMISOS = {
    "dr_gomez":  {"ver_pacientes": True},
    "enfermeria": {"ver_pacientes": False},
}

CAMPOS_PII = ["nombre", "dni", "telefono"]


def validar(patient_id):
    """Gesto 1: el pedido tiene forma válida y no es un ataque."""
    if not isinstance(patient_id, int) or patient_id <= 0:
        raise ValueError(f"ID de paciente inválido: {patient_id!r}")
    return patient_id


def autorizar(usuario):
    """Gesto 2: este profesional tiene permiso para ver fichas."""
    permiso = PERMISOS.get(usuario, {})
    if not permiso.get("ver_pacientes", False):
        raise PermissionError(f"El usuario {usuario!r} no está autorizado a ver pacientes.")
    return usuario


def ejecutar(patient_id):
    """Gesto 3: leer de la base en modo SOLO LECTURA."""
    conexion = sqlite3.connect(f"file:{RUTA_BASE}?mode=ro", uri=True)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM pacientes WHERE id = ?", (patient_id,))
    fila = cursor.fetchone()
    conexion.close()
    if fila is None:
        raise LookupError(f"No existe paciente con id {patient_id}.")
    return dict(fila)


def sanitizar(ficha):
    """Gesto 4: tachar la PII antes de que el dato salga hacia el LLM."""
    ficha_limpia = dict(ficha)
    for campo in CAMPOS_PII:
        if campo in ficha_limpia:
            ficha_limpia[campo] = "[DATO PROTEGIDO]"
    return ficha_limpia


def auditar(usuario, patient_id, resultado):
    """Gesto 5: dejar registro de quién pidió qué y cuándo."""
    momento = datetime.now().isoformat(timespec="seconds")
    linea = f"{momento} | usuario={usuario} | paciente={patient_id} | {resultado}\n"
    with open(RUTA_AUDITORIA, "a", encoding="utf-8") as archivo:
        archivo.write(linea)


def consultar_paciente(usuario, patient_id):
    """El archivista completo: los cinco gestos en orden."""
    try:
        patient_id = validar(patient_id)
        autorizar(usuario)
        ficha = ejecutar(patient_id)
        ficha_segura = sanitizar(ficha)
        auditar(usuario, patient_id, "OK")
        return ficha_segura
    except (ValueError, PermissionError, LookupError) as error:
        auditar(usuario, patient_id, f"RECHAZADO: {error}")
        raise


if __name__ == "__main__":
    print("1) Caso OK (médico autorizado, paciente existente):")
    print(consultar_paciente("dr_gomez", 1))

    print("\n2) Usuario SIN permiso:")
    try:
        consultar_paciente("enfermeria", 1)
    except PermissionError as e:
        print(f"   Rechazado como se esperaba -> {e}")

    print("\n3) Paciente que NO existe:")
    try:
        consultar_paciente("dr_gomez", 999)
    except LookupError as e:
        print(f"   Rechazado como se esperaba -> {e}")

    print("\n4) ID inválido (intento de inyección / basura):")
    try:
        consultar_paciente("dr_gomez", "1 OR 1=1")
    except ValueError as e:
        print(f"   Rechazado como se esperaba -> {e}")