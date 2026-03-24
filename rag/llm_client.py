import requests

from app.config import LLM_API_URL, LLM_API_KEY, LLM_MODEL, LLM_TIMEOUT_SECONDS


def is_llm_configured() -> bool:
    return bool(LLM_API_URL and LLM_API_KEY and LLM_MODEL)


def build_rag_prompt(question: str, context_chunks: list[str]) -> str:
    context = "\n\n".join(
        [f"[Source {i+1}] {chunk}" for i, chunk in enumerate(context_chunks)]
    )

    return f"""You are answering questions about job postings.

Use only the provided context.
Do not invent facts.
If the context is insufficient, say so briefly.

Question:
{question}

Context:
{context}

Answer in a concise and clear way.
"""


def generate_with_llm(question: str, context_chunks: list[str]) -> str:
    if not is_llm_configured():
        raise RuntimeError("LLM is not configured")

    prompt = build_rag_prompt(question, context_chunks)

    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "temperature": 0.2,
        "max_tokens": 300,
    }

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        LLM_API_URL,
        json=payload,
        headers=headers,
        timeout=LLM_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    data = response.json()

    if "text" in data and isinstance(data["text"], str):
        return data["text"].strip()

    if "output" in data and isinstance(data["output"], str):
        return data["output"].strip()

    if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
        first = data["choices"][0]
        if isinstance(first, dict):
            if "text" in first and isinstance(first["text"], str):
                return first["text"].strip()
            if "message" in first and isinstance(first["message"], dict):
                content = first["message"].get("content")
                if isinstance(content, str):
                    return content.strip()

    raise RuntimeError("Unexpected LLM response shape")