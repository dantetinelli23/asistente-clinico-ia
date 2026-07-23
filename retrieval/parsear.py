# retrieval/parsear.py
# Se corre UNA sola vez: convierte el PDF crudo a Markdown limpio
# (respetando titulos, listas y tablas) y lo guarda en disco.
# Corre 100% local: no usa nube ni API keys.
#
# Motor de parseo: Docling (IBM Research), en vez de pymupdf4llm.
# Por que el cambio: pymupdf4llm dejaba las tablas mal formadas
# (notas al pie sueltas, filas con <br> rotos). Docling reconstruye
# la tabla real con un modelo especializado (TableFormer) y detecta
# que notas al pie pertenecen a que tabla.

import re
from docling.document_converter import DocumentConverter
from docling_core.types.doc import TableItem

# --- 1. Parsear el PDF con Docling ---
print("Parseando el PDF... (puede tardar unos segundos)")
conversor = DocumentConverter()
resultado = conversor.convert("data/guia_hta.pdf")
documento = resultado.document

# --- 2. Arreglar el bug conocido de Docling: las notas al pie de las
#         tablas se detectan bien por dentro, pero export_to_markdown()
#         no las incluye en el texto de salida. Las inyectamos a mano,
#         adentro de la celda correspondiente, para que viajen pegadas
#         al dato aunque despues se trocee el documento en chunks.
print("Revisando tablas con notas al pie...")
tablas_corregidas = 0
notas_incrustadas = 0

for item, _ in documento.iterate_items():
    if isinstance(item, TableItem) and len(item.footnotes) > 0:
        tablas_corregidas += 1
        for referencia_nota in item.footnotes:
            nota = referencia_nota.resolve(documento)
            texto_nota = nota.text

            coincidencia = re.match(r"^(\*+)\s*(.*)", texto_nota)
            if not coincidencia:
                continue
            simbolo = coincidencia.group(1)
            mensaje = coincidencia.group(2).strip()

            for celda in item.data.table_cells:
                simbolo_celda = re.search(r"(\*+)$", celda.text)
                if simbolo_celda and simbolo_celda.group(1) == simbolo:
                    valor_limpio = celda.text[:-len(simbolo)]
                    celda.text = f"{valor_limpio} ({mensaje})"
                    notas_incrustadas += 1

print(f"  Tablas con notas encontradas: {tablas_corregidas}")
print(f"  Notas incrustadas en su celda: {notas_incrustadas}")

# --- 3. Exportar a Markdown, ya con las tablas corregidas ---
texto_markdown = documento.export_to_markdown()

# --- 4. Guardar el resultado limpio en disco ---
with open("data/guia_hta.md", "w", encoding="utf-8") as archivo:
    archivo.write(texto_markdown)

print(f"Listo. Se guardaron {len(texto_markdown)} caracteres en data/guia_hta.md")