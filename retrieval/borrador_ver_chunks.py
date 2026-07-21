# retrieval/ver_chunks.py
# Herramienta de inspeccion: abre la base ya creada y muestra los chunks
# guardados, para revisar a ojo si el corte semantico quedo bien.
# NO reconstruye nada ni llama a Cohere: solo lee del disco.

from dotenv import load_dotenv
load_dotenv()

from langchain_cohere import CohereEmbeddings
from langchain_chroma import Chroma

# Abrimos la base que YA existe (ojo: esto es distinto a crearla).
embeddings = CohereEmbeddings(model="embed-multilingual-v3.0")
base_vectorial = Chroma(
    persist_directory="chroma_db",
    embedding_function=embeddings,
)

# Traemos todo lo guardado. Nos quedamos con la lista de textos.
datos = base_vectorial.get()
chunks = datos["documents"]

print(f"Hay {len(chunks)} chunks guardados.\n")

for i, chunk in enumerate(chunks):
    print("=" * 70)
    print(f"CHUNK {i}  ({len(chunk)} caracteres)")
    print("=" * 70)
    print(chunk)
    print()