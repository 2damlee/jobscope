from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]):
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)


def embed_query(text: str):
    return model.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]