# retrieval/buscar_hibrido.py
# Arma el buscador HIBRIDO (denso + BM25) y lo prueba con una pregunta.
# No modifica la base: solo LEE lo que indexar.py ya dejo guardado.

from dotenv import load_dotenv
load_dotenv()

from langchain_cohere import CohereEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

# --- 1. Abrir la base vectorial ya existente (busqueda DENSA) ---
embeddings = CohereEmbeddings(model="embed-multilingual-v3.0")
base_vectorial = Chroma(
    persist_directory="chroma_db",
    embedding_function=embeddings,
)
buscador_denso = base_vectorial.as_retriever(search_kwargs={"k": 5})

# --- 2. Armar el buscador BM25 (busqueda por palabras) ---
# BM25 necesita los textos en memoria, no vive en Chroma: se lo damos aparte.
todos_los_chunks = base_vectorial.get()["documents"]
buscador_bm25 = BM25Retriever.from_texts(todos_los_chunks)
buscador_bm25.k = 5

# --- 3. Fusionar ambos en un buscador HIBRIDO ---
buscador_hibrido = EnsembleRetriever(
    retrievers=[buscador_denso, buscador_bm25],
    weights=[0.5, 0.5],
)

# --- 4. Probarlo con una pregunta ---
pregunta = "¿desde que valores de presion se considera hipertension?"
resultados = buscador_hibrido.invoke(pregunta)

print(f"Pregunta: {pregunta}\n")
print(f"Se encontraron {len(resultados)} resultados combinados:\n")
for i, doc in enumerate(resultados):
    print("=" * 70)
    print(f"RESULTADO {i}")
    print("=" * 70)
    print(doc.page_content[:400])
    print()