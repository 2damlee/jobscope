import re


def clean_description(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s\-\./]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()