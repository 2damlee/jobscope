from collections import Counter
import re


def split_sentences(text: str) -> list[str]:
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def extract_top_terms(chunks: list[str], stopwords: set[str] | None = None, top_n: int = 5) -> list[str]:
    if stopwords is None:
        stopwords = {
            "the", "and", "for", "with", "using", "use", "work", "build",
            "data", "job", "role", "required", "preferred", "experience",
            "python", "based", "support", "team", "systems", "services"
        }

    counter = Counter()

    for chunk in chunks:
        words = re.findall(r"\b[a-zA-Z][a-zA-Z\-\+\.]+\b", chunk.lower())
        for word in words:
            if word not in stopwords and len(word) > 2:
                counter[word] += 1

    return [word for word, _ in counter.most_common(top_n)]


def summarize_jobs(results: list[dict]) -> str:
    lines = []
    seen = set()

    for r in results:
        key = (r["job_id"], r["title"])
        if key in seen:
            continue
        seen.add(key)

        sentence = split_sentences(r["chunk_text"])
        summary_text = sentence[0] if sentence else r["chunk_text"]
        lines.append(f"- {r['title']} ({r['location']}): {summary_text}")

    return "\n".join(lines)


def summarize_common_skills(results: list[dict]) -> str:
    chunks = [r["chunk_text"] for r in results]
    top_terms = extract_top_terms(chunks, top_n=6)

    lines = []
    if top_terms:
        lines.append("Common themes across the retrieved postings include: " + ", ".join(top_terms) + ".")

    lines.append("Relevant examples:")
    lines.append(summarize_jobs(results))

    return "\n".join(lines)


def detect_question_type(question: str) -> str:
    q = question.lower()

    if "skill" in q or "common requirements" in q or "common qualifications" in q:
        return "skills"

    if q.startswith("which") or "which jobs" in q or "what jobs" in q:
        return "jobs"

    return "general"


def generate_answer(question: str, results: list[dict]) -> str:
    if not results:
        return "No relevant job posting information was found for the given question and filters."

    question_type = detect_question_type(question)

    if question_type == "skills":
        return summarize_common_skills(results)

    if question_type == "jobs":
        return "Relevant job postings:\n" + summarize_jobs(results)

    return "Based on the retrieved job postings:\n" + summarize_jobs(results)