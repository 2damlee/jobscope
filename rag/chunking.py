import re


def split_into_sentences(text: str) -> list[str]:
    if not text:
        return []

    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def merge_short_sentences(sentences: list[str], min_sentence_length: int = 40) -> list[str]:
    if not sentences:
        return []

    merged = []
    buffer = ""

    for sentence in sentences:
        if len(sentence) < min_sentence_length:
            if buffer:
                buffer += " " + sentence
            else:
                buffer = sentence
        else:
            if buffer:
                merged.append(buffer.strip())
                buffer = ""
            merged.append(sentence)

    if buffer:
        if merged:
            merged[-1] = merged[-1] + " " + buffer
        else:
            merged.append(buffer)

    return merged


def chunk_text(
    text: str,
    target_chunk_size: int = 320,
    max_chunk_size: int = 420,
    overlap_sentences: int = 1,
) -> list[str]:
    if not text:
        return []

    sentences = split_into_sentences(text)
    sentences = merge_short_sentences(sentences)

    if not sentences:
        return []

    chunks = []
    current_chunk = []

    for sentence in sentences:
        candidate = " ".join(current_chunk + [sentence]).strip()

        if len(candidate) <= max_chunk_size:
            current_chunk.append(sentence)
            continue

        if current_chunk:
            chunks.append(" ".join(current_chunk).strip())

        if overlap_sentences > 0 and chunks:
            overlap = current_chunk[-overlap_sentences:] if len(current_chunk) >= overlap_sentences else current_chunk
            current_chunk = overlap + [sentence]
        else:
            current_chunk = [sentence]

    if current_chunk:
        chunks.append(" ".join(current_chunk).strip())

    cleaned_chunks = []
    for chunk in chunks:
        chunk = re.sub(r"\s+", " ", chunk).strip()
        if len(chunk) >= 40:
            cleaned_chunks.append(chunk)

    return cleaned_chunks