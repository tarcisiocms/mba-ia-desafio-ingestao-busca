from langchain_google_genai import ChatGoogleGenerativeAI

from config import LLM_MODEL, build_vector_store, require_google_api_key


NO_CONTEXT_RESPONSE = "Nao tenho informacoes necessarias para responder sua pergunta."

PROMPT_TEMPLATE = """CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informacao nao estiver explicitamente no CONTEXTO, responda:
  "Nao tenho informacoes necessarias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opinioes ou interpretacoes alem do que esta escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual e a capital da Franca?"
Resposta: "Nao tenho informacoes necessarias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Nao tenho informacoes necessarias para responder sua pergunta."

Pergunta: "Voce acha isso bom ou ruim?"
Resposta: "Nao tenho informacoes necessarias para responder sua pergunta."

PERGUNTA DO USUARIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUARIO"
"""


def search_documents(question: str):
    vector_store = build_vector_store()
    return vector_store.similarity_search_with_score(question, k=10)


def build_context(results) -> str:
    return "\n\n".join(document.page_content for document, _score in results).strip()


def answer_question(question: str) -> str:
    require_google_api_key()
    results = search_documents(question)
    context = build_context(results)

    if not context:
        return NO_CONTEXT_RESPONSE

    prompt = PROMPT_TEMPLATE.format(contexto=context, pergunta=question)
    response = ChatGoogleGenerativeAI(model=LLM_MODEL).invoke(prompt)
    return response.content.strip()


def search_prompt(question=None):
    if question is None:
        return answer_question

    return answer_question(question)
