from __future__ import annotations


def parse_skills(skills: str | None) -> set[str]:
    if not skills:
        return set()
    return {skill.strip() for skill in skills.split(",") if skill.strip()}


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def compute_hybrid_score(
    embedding_score: float,
    target_skills: set[str],
    candidate_skills: set[str],
    same_category: bool,
    same_seniority: bool,
) -> dict:
    skill_overlap = jaccard_similarity(target_skills, candidate_skills)

    category_bonus = 1.0 if same_category else 0.0
    seniority_bonus = 1.0 if same_seniority else 0.0

    final_score = (
        0.70 * embedding_score
        + 0.20 * skill_overlap
        + 0.07 * category_bonus
        + 0.03 * seniority_bonus
    )

    return {
        "final_score": round(final_score, 4),
        "embedding_score": round(embedding_score, 4),
        "skill_overlap_score": round(skill_overlap, 4),
    }