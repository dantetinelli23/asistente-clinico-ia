# retrieval/buscar_con_rerank.py
# Toma los candidatos del buscador HIBRIDO y los reordena con un
# reranker (lectura fina, par por par, de pregunta vs cada candidato).

from dotenv import load_dotenv
load_dotenv()

from langchain_cohere import CohereEmbeddings, CohereRerank
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_classic.retrievers import ContextualCompressionRetriever

# --- 1. Reconstruir el buscador HIBRIDO (igual que en buscar_hibrido.py) ---
embeddings = CohereEmbeddings(model="embed-multilingual-v3.0")
base_vectorial = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
buscador_denso = base_vectorial.as_retriever(search_kwargs={"k": 5})

todos_los_chunks = base_vectorial.get()["documents"]
buscador_bm25 = BM25Retriever.from_texts(todos_los_chunks)
buscador_bm25.k = 5

buscador_hibrido = EnsembleRetriever(
    retrievers=[buscador_denso, buscador_bm25],
    weights=[0.5, 0.5],
)

# --- 2. Envolver el hibrido con el RERANKER ---
reranker = CohereRerank(model="rerank-v3.5", top_n=3)

buscador_final = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=buscador_hibrido,
)

# --- 3. Probar con la misma pregunta de antes ---
pregunta = "¿desde que valores de presion se considera hipertension?"
resultados = buscador_final.invoke(pregunta)

print(f"Pregunta: {pregunta}\n")
print(f"El reranker devolvio los {len(resultados)} mejores, en orden:\n")
for i, doc in enumerate(resultados):
    puntaje = doc.metadata.get("relevance_score", "N/A")
    print("=" * 70)
    print(f"PUESTO {i}  (relevance_score: {puntaje})")
    print("=" * 70)
    print(doc.page_content[:400])
    print()