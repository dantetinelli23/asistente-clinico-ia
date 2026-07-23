# ranking/reranker.py
# El re-ranking del pipeline RAG: un segundo filtro, mas fino y mas caro,
# que reordena los candidatos de la busqueda por relevancia real
# (cross-encoder, ver Fase 1-2 para la teoria completa).

from langchain_cohere import CohereRerank
from langchain_classic.retrievers import ContextualCompressionRetriever


def aplicar_reranking(buscador_base, top_n: int = 3, modelo: str = "rerank-v3.5"):
    """Envuelve un buscador (retriever) cualquiera con un reranker de Cohere.
    Recibe el buscador base (por ejemplo el hibrido de denso+BM25) y devuelve
    un buscador nuevo: al consultarlo, primero trae los candidatos del
    buscador base y despues los reordena, quedandose con los top_n mas
    relevantes segun el cross-encoder."""
    reranker = CohereRerank(model=modelo, top_n=top_n)
    return ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=buscador_base,
    )