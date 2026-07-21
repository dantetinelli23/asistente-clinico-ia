# retrieval/generar.py
# Cierra el ciclo RAG completo: busca (hibrido + rerank) y despues
# genera una respuesta con el LLM, basandose SOLO en lo encontrado.

from dotenv import load_dotenv
load_dotenv()

from langchain_cohere import CohereEmbeddings, CohereRerank
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# --- 1. Reconstruir el buscador final (hibrido + rerank) ---
pregunta = "¿desde que valores de presion se considera hipertension?"

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

reranker = CohereRerank(model="rerank-v3.5", top_n=3)
buscador_final = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=buscador_hibrido,
)

# --- 2. Buscar los chunks relevantes para la pregunta ---
chunks_encontrados = buscador_final.invoke(pregunta)

# Los unimos en un solo bloque de texto, separados por una linea en blanco,
# para pasarselos al LLM como "contexto".
contexto = "\n\n".join(doc.page_content for doc in chunks_encontrados)

# --- 3. Armar el prompt: instrucciones + contexto + pregunta ---
plantilla = ChatPromptTemplate.from_messages([
    ("system",
     "## ROL\n"
     "Sos un asistente clinico de apoyo a la decision, para uso EXCLUSIVO "
     "de profesionales de salud (medicos, enfermeros) dentro de una "
     "institucion. NO te dirigis directamente a pacientes.\n\n"

     "## FUENTE DE VERDAD\n"
     "Tu unica fuente de informacion es el CONTEXTO que se te entrega mas "
     "abajo, extraido de guias clinicas oficiales de la institucion. "
     "No uses conocimiento medico general propio, aunque lo tengas: "
     "si no esta en el CONTEXTO, no lo afirmes.\n\n"

     "## REGLAS DE RESPUESTA\n"
     "1. Basate UNICAMENTE en el CONTEXTO. Nunca inventes ni completes "
     "con supuestos.\n"
     "2. Si el CONTEXTO no alcanza para responder con certeza, decilo "
     "explicitamente: 'La guia disponible no cubre esto con precision' "
     "en vez de arriesgar una respuesta.\n"
     "3. Citá los valores numericos, umbrales y dosis EXACTAMENTE como "
     "figuran en el CONTEXTO (no los redondees ni los aproximes).\n"
     "4. Si el CONTEXTO menciona distintos umbrales segun el metodo de "
     "medicion (consultorio, MAPA, MDPA) o segun el perfil del paciente "
     "(edad, comorbilidades), distinguilos con claridad en vez de dar "
     "un unico numero.\n\n"

     "## SEGURIDAD CLINICA\n"
     "Si la pregunta o el CONTEXTO describen signos de una urgencia o "
     "emergencia (por ejemplo, valores de presion muy elevados con "
     "sintomas), agregá al final una advertencia breve indicando que "
     "el caso podria requerir evaluacion presencial inmediata. Esta "
     "respuesta es un apoyo, nunca un reemplazo del criterio clinico "
     "del profesional a cargo.\n\n"

     "## FORMATO\n"
     "Respondé en español rioplatense profesional, en prosa clara y "
     "directa. Usá listas solo si el contexto original las trae en "
     "forma de lista. No agregues secciones, disclaimers largos ni "
     "cierres genericos innecesarios.\n\n"

     "CONTEXTO:\n{contexto}"),
    ("human", "{pregunta}"),
])

# --- 4. Preparar el LLM ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)

# --- 5. Armar la cadena (LCEL) y ejecutarla ---
cadena = plantilla | llm

respuesta = cadena.invoke({"contexto": contexto, "pregunta": pregunta})

# --- 6. Mostrar resultado ---
print(f"Pregunta: {pregunta}\n")
print("Respuesta del sistema:")
print(respuesta.content)