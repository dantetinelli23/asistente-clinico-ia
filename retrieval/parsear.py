# retrieval/parsear.py
# Se corre UNA sola vez: convierte el PDF crudo a Markdown limpio
# (respetando titulos, listas y tablas) y lo guarda en disco.
# Corre 100% local: no usa nube ni API keys.

import pymupdf4llm

# --- 1. Parsear el PDF a texto Markdown ---
print("Parseando el PDF... (puede tardar unos segundos)")
texto_markdown = pymupdf4llm.to_markdown("data/guia_hta.pdf")

# --- 2. Guardar el resultado limpio en disco ---
with open("data/guia_hta.md", "w", encoding="utf-8") as archivo:
    archivo.write(texto_markdown)

print(f"Listo. Se guardaron {len(texto_markdown)} caracteres en data/guia_hta.md")