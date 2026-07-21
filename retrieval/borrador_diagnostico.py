# retrieval/diagnostico.py
# Busca directamente, entre TODOS los chunks guardados, cuales contienen
# el texto "140/90". No usa IA ni busqueda: es un grep simple, para saber
# si el dato existe en la base antes de sospechar del buscador.

from dotenv import load_dotenv
load_dotenv()

from langchain_cohere import CohereEmbeddings
from langchain_chroma import Chroma

embeddings = CohereEmbeddings(model="embed-multilingual-v3.0")
base_vectorial = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
chunks = base_vectorial.get()["documents"]

print(f"Total de chunks en la base: {len(chunks)}\n")

encontrados = 0
for i, chunk in enumerate(chunks):
    if "140/90" in chunk:
        encontrados += 1
        print(f"--- Chunk {i} ({len(chunk)} caracteres) CONTIENE '140/90' ---")
        print(chunk[:300])
        print()

if encontrados == 0:
    print("NINGUN chunk contiene '140/90'. El dato no llego a la base.")