import os

import psycopg
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector


load_dotenv()

EMBEDDING_MODEL_ALIASES = {
    "models/embedding-001": "gemini-embedding-001",
    "embedding-001": "gemini-embedding-001",
}

EMBEDDING_MODEL = EMBEDDING_MODEL_ALIASES.get(
    os.getenv("GOOGLE_EMBEDDING_MODEL", "gemini-embedding-001"),
    os.getenv("GOOGLE_EMBEDDING_MODEL", "gemini-embedding-001"),
)
LLM_MODEL = os.getenv("GOOGLE_LLM_MODEL", "gemini-2.5-flash-lite")
COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME", "pdf_chunks")


def require_google_api_key() -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            "GOOGLE_API_KEY nao configurada. Crie um arquivo .env a partir de "
            ".env.example e preencha sua chave do Gemini antes de executar "
            "ingestao ou chat."
        )


def database_url() -> str:
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "desafio01-db")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "rag")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"


def psycopg_url() -> str:
    return database_url().replace("postgresql+psycopg://", "postgresql://", 1)


def ensure_pgvector_extension() -> None:
    with psycopg.connect(psycopg_url()) as connection:
        connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
        connection.commit()


def build_embeddings() -> GoogleGenerativeAIEmbeddings:
    require_google_api_key()
    return GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)


def build_vector_store() -> PGVector:
    ensure_pgvector_extension()
    return PGVector(
        embeddings=build_embeddings(),
        collection_name=COLLECTION_NAME,
        connection=database_url(),
        use_jsonb=True,
    )
