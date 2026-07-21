from mcp.server.fastmcp import FastMCP
from adaptadores_mcp.adaptador_seguro import consultar_paciente

mcp = FastMCP("asistente-clinico")


@mcp.tool()
def obtener_ficha_paciente(usuario: str, patient_id: int) -> dict:
    """Devuelve la ficha clínica de un paciente con los datos personales protegidos.

    Solo para profesionales autorizados. Todo acceso queda auditado.
    """
    try:
        return consultar_paciente(usuario, patient_id)
    except Exception as error:
        return {"error": str(error)}


if __name__ == "__main__":
    mcp.run()