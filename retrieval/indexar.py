# retrieval/indexar.py
# Se corre UNA sola vez: lee el texto limpio, lo trocea en dos etapas
# (semantico + tope de tamaño de seguridad) y lo guarda indexado.

from dotenv import load_dotenv
load_dotenv()

from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_chroma import Chroma

# --- 1. Leer el texto limpio que dejo parsear.py ---
with open("data/guia_hta.md", "r", encoding="utf-8") as archivo:
    texto_completo = archivo.read()

print(f"Se leyeron {len(texto_completo)} caracteres del Markdown.")

# --- 2. Preparar el modelo de embeddings de Cohere ---
embeddings = CohereEmbeddings(model="embed-multilingual-v3.0")

# --- 3a. Primera pasada: chunking SEMANTICO (corta por tema) ---
troceador_semantico = SemanticChunker(embeddings)
chunks_semanticos = troceador_semantico.create_documents([texto_completo])
print(f"Chunking semantico: {len(chunks_semanticos)} chunks.")

# --- 3b. Segunda pasada: tope de seguridad por tamaño ---
# Cualquier chunk semantico que haya quedado gigante (mezclando temas)
# se re-corta aca, para que ningun chunk final supere el limite.
troceador_de_respaldo = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
chunks = troceador_de_respaldo.split_documents(chunks_semanticos)
print(f"Tras el tope de seguridad: {len(chunks)} chunks finales.")

# --- 4. Embeder e indexar los chunks en Chroma (se guarda en disco) ---
base_vectorial = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="chroma_db",
)
print("Base vectorial creada en la carpeta 'chroma_db'. Listo.")