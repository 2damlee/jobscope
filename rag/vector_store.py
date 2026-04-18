import faiss
import numpy as np

from app.config import CHUNK_INDEX_PATH

INDEX_PATH = str(CHUNK_INDEX_PATH)


def build_faiss_index(vectors: np.ndarray):
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    return index


def save_faiss_index(index, path: str = INDEX_PATH):
    faiss.write_index(index, path)


def load_faiss_index(path: str = INDEX_PATH):
    return faiss.read_index(path)