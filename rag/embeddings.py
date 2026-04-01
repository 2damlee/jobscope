from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]):
    model = get_model()
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)


def embed_query(text: str):
    model = get_model()
    return model.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]