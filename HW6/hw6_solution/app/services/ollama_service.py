import httpx

from ..config import settings


class OllamaError(Exception):
    pass


def _post(endpoint: str, payload: dict) -> dict:
    base = settings.OLLAMA_BASE_URL.rstrip("/")
    url = f"{base}{endpoint}"

    try:
        with httpx.Client(timeout=settings.OLLAMA_TIMEOUT_SECS) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise OllamaError(f"Ollama request failed: {exc}") from exc
    except ValueError as exc:
        raise OllamaError(f"Invalid JSON from Ollama: {exc}") from exc


def chat(model: str, messages: list[dict], temperature: float = 0.2) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    data = _post("/api/chat", payload)

    content = (data.get("message") or {}).get("content")
    if not content:
        raise OllamaError("Ollama /api/chat returned empty message content.")
    return content.strip()


def embed(text: str, model: str | None = None) -> list[float]:
    payload = {
        "model": model or settings.EMBED_MODEL,
        "prompt": text,
    }
    data = _post("/api/embeddings", payload)

    vec = data.get("embedding")
    if not isinstance(vec, list) or not vec:
        raise OllamaError("Ollama /api/embeddings returned empty embedding.")

    try:
        return [float(v) for v in vec]
    except (TypeError, ValueError) as exc:
        raise OllamaError("Embedding contains non-numeric values.") from exc
