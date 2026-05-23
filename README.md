# Desafio MBA Engenharia de Software com IA - Full Cycle

Esta solucao roda inteiramente em containers Docker. Nao crie virtualenv no host,
nao execute `pip install` no host e nao instale PostgreSQL localmente.

## Requisitos

- Docker
- Docker Compose

## Configuracao

Crie o arquivo `.env` a partir de `.env.example` e informe sua chave:

```bash
cp .env.example .env
```

Preencha `GOOGLE_API_KEY` no `.env`.

Os modelos configurados por padrao sao:

- Embeddings: `gemini-embedding-001`
- LLM: `gemini-2.5-flash-lite`

Para testar outro modelo de resposta, altere `GOOGLE_LLM_MODEL` no `.env`, por
exemplo para `gemini-3.1-flash-lite-preview` se ele estiver disponivel na sua
conta/projeto.

O arquivo `document.pdf` deve ficar na raiz do projeto. Este fork ja contem um
`document.pdf`; substitua-o se quiser indexar outro documento.

A ingestao envia embeddings em lotes para reduzir risco de rate limit. Os
valores padrao sao:

- `INGEST_BATCH_SIZE=5`
- `INGEST_BATCH_DELAY_SECONDS=1`
- `INGEST_MAX_TOKENS_PER_MINUTE=20000`

Se a Gemini API retornar `RESOURCE_EXHAUSTED`, reduza o tamanho do lote, aumente
o intervalo entre lotes, reduza `INGEST_MAX_TOKENS_PER_MINUTE` para um valor
abaixo da sua quota de TPM ou revise a quota/billing da chave.

## Execucao

Suba o banco PostgreSQL com pgVector:

```bash
docker compose up -d desafio01-db
```

Construa a aplicacao. O virtualenv Python e criado dentro do container em
`/opt/venv`:

```bash
docker compose build desafio01-app
```

Execute a ingestao:

```bash
docker compose run --rm desafio01-app python src/ingest.py
```

Execute o chat:

```bash
docker compose run --rm desafio01-app python src/chat.py
```

No chat, digite perguntas no terminal. Para encerrar, use `sair`, `exit` ou `q`.

Perguntas sem resposta explicita no PDF devem retornar exatamente:

```text
Nao tenho informacoes necessarias para responder sua pergunta.
```
