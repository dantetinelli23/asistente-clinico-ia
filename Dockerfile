FROM python:3.13-slim

WORKDIR /app

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY api.py .
COPY agente/ agente/
COPY retrieval/ retrieval/
COPY chroma_db/ chroma_db/
COPY ranking/ ranking/
COPY frontend/ frontend/
COPY orquestacion/ orquestacion/

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]