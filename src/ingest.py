import hashlib
import os
import sys
import time
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from config import build_vector_store


PDF_PATH = Path(os.getenv("PDF_PATH", "document.pdf"))
BATCH_SIZE = int(os.getenv("INGEST_BATCH_SIZE", "5"))
BATCH_DELAY_SECONDS = float(os.getenv("INGEST_BATCH_DELAY_SECONDS", "1"))
MAX_TOKENS_PER_MINUTE = int(os.getenv("INGEST_MAX_TOKENS_PER_MINUTE", "20000"))


class TokenWindowThrottle:
    def __init__(self, max_tokens_per_minute: int) -> None:
        self.max_tokens_per_minute = max_tokens_per_minute
        self.window_started_at = time.monotonic()
        self.tokens_used = 0

    def wait_if_needed(self, estimated_tokens: int) -> None:
        if self.max_tokens_per_minute <= 0:
            return

        now = time.monotonic()
        elapsed = now - self.window_started_at

        if elapsed >= 60:
            self.window_started_at = now
            self.tokens_used = 0
            elapsed = 0

        if self.tokens_used + estimated_tokens <= self.max_tokens_per_minute:
            self.tokens_used += estimated_tokens
            return

        sleep_seconds = max(0, 60 - elapsed)
        print(
            "Aguardando limite de tokens da Gemini API "
            f"({sleep_seconds:.0f}s)...",
            flush=True,
        )
        time.sleep(sleep_seconds)
        self.window_started_at = time.monotonic()
        self.tokens_used = estimated_tokens


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 2)


def chunk_id(content: str, index: int) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"document-pdf-{index}-{digest}"


def load_pdf(path: Path) -> list[Document]:
    reader = PdfReader(str(path))
    documents = []

    for page_index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if not text.strip():
            continue

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(path),
                    "page": page_index,
                    "total_pages": len(reader.pages),
                },
            )
        )

    return documents


def ingest_pdf() -> int:
    if not PDF_PATH.exists():
        raise FileNotFoundError(
            "O arquivo document.pdf deve estar na raiz do projeto antes da ingestao."
        )

    pages = load_pdf(PDF_PATH)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(pages)

    for index, chunk in enumerate(chunks):
        chunk.metadata["source"] = str(PDF_PATH)
        chunk.metadata["chunk_index"] = index

    vector_store = build_vector_store()
    ids = [chunk_id(chunk.page_content, index) for index, chunk in enumerate(chunks)]
    throttle = TokenWindowThrottle(MAX_TOKENS_PER_MINUTE)

    try:
        for start in range(0, len(chunks), BATCH_SIZE):
            end = start + BATCH_SIZE
            batch = chunks[start:end]
            estimated_tokens = sum(estimate_tokens(chunk.page_content) for chunk in batch)

            throttle.wait_if_needed(estimated_tokens)
            vector_store.add_documents(chunks[start:end], ids=ids[start:end])
            print(
                f"Ingeridos {min(end, len(chunks))}/{len(chunks)} chunks.",
                flush=True,
            )

            if end < len(chunks) and BATCH_DELAY_SECONDS > 0:
                time.sleep(BATCH_DELAY_SECONDS)
    except Exception as error:
        message = str(error)

        if "RESOURCE_EXHAUSTED" in message or "429" in message:
            raise RuntimeError(
                "A API do Gemini retornou limite de quota ou rate limit durante "
                "a geracao de embeddings. Tente novamente mais tarde, reduza "
                "INGEST_BATCH_SIZE, aumente INGEST_BATCH_DELAY_SECONDS ou revise "
                "a quota/billing da chave configurada."
            ) from error

        if "NOT_FOUND" in message or "404" in message:
            raise RuntimeError(
                "O modelo de embeddings configurado nao esta disponivel para "
                "embedContent na Gemini API. Use GOOGLE_EMBEDDING_MODEL="
                "gemini-embedding-001."
            ) from error

        raise

    return len(chunks)


if __name__ == "__main__":
    try:
        total = ingest_pdf()
    except RuntimeError as error:
        print(f"Erro na ingestao: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Ingestao concluida. {total} chunks processados.")
