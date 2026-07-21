# retrieval/buscador.py
# Empaqueta el RAG completo de la Fase 2 (hibrido + rerank) en una funcion
# reutilizable. El buscador se arma UNA vez al importar; buscar_protocolos()
# solo lo USA en cada llamada.

from dotenv import load_dotenv
load_dotenv()

from langchain_cohere import CohereEmbeddings, CohereRerank
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever

# --- SE ARMA UNA SOLA VEZ (al importar este archivo) ---

embeddings = CohereEmbeddings(model="embed-multilingual-v3.0")
base_vectorial = Chroma(persist_directory="chroma_db", embedding_function=embeddings)

buscador_denso = base_vectorial.as_retriever(search_kwargs={"k": 10})

todos_los_chunks = base_vectorial.get()["documents"]
buscador_bm25 = BM25Retriever.from_texts(todos_los_chunks)
buscador_bm25.k = 10

buscador_hibrido = EnsembleRetriever(
    retrievers=[buscador_denso, buscador_bm25],
    weights=[0.5, 0.5],
)

reranker = CohereRerank(model="rerank-v3.5", top_n=3)
buscador_final = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=buscador_hibrido,
)


# --- SE USA EN CADA LLAMADA ---

def buscar_protocolos(pregunta: str) -> list[str]:
    """Busca en los protocolos clinicos y devuelve los chunks mas relevantes
    como una lista de textos. Recibe la pregunta, devuelve los textos."""
    documentos = buscador_final.invoke(pregunta)
    return [doc.page_content for doc in documentos]