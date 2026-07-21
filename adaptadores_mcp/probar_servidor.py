import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    parametros = StdioServerParameters(
        command="python",
        args=["-m", "adaptadores_mcp.servidor_mcp"],
    )
    async with stdio_client(parametros) as (leer, escribir):
        async with ClientSession(leer, escribir) as sesion:
            await sesion.initialize()

            herramientas = await sesion.list_tools()
            print("Herramientas expuestas:", [h.name for h in herramientas.tools])

            resultado = await sesion.call_tool(
                "obtener_ficha_paciente",
                {"usuario": "dr_gomez", "patient_id": 1},
            )
            print("\nResultado de la herramienta:")
            print(resultado.content)


asyncio.run(main())