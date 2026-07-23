import re
from docling.document_converter import DocumentConverter
from docling_core.types.doc import TableItem

conversor = DocumentConverter()
resultado = conversor.convert("data/guia_hta.pdf")
documento = resultado.document

for item, _ in documento.iterate_items():
    if isinstance(item, TableItem) and len(item.footnotes) > 0:
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

markdown_corregido = documento.export_to_markdown()

with open("data/guia_hta_corregido.md", "w", encoding="utf-8") as archivo:
    archivo.write(markdown_corregido)

print("Listo. Revisá data/guia_hta_corregido.md")