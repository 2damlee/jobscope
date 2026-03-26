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


def build_recommendation_rows(
    *,
    target_job,
    target_skills: set[str],
    embedding_job_ids: list[int],
    embedding_scores,
    candidate_map: dict[int, object],
    limit: int,
    same_category_only: bool,
) -> list[dict]:
    ranked = []

    for idx, embedding_score in enumerate(embedding_scores):
        candidate_id = embedding_job_ids[idx]
        if candidate_id == target_job.id:
            continue

        candidate_job = candidate_map.get(candidate_id)
        if not candidate_job or not candidate_job.title:
            continue

        same_category = (target_job.category or "") == (candidate_job.category or "")
        same_seniority = (target_job.seniority or "") == (candidate_job.seniority or "")

        if same_category_only and not same_category:
            continue

        candidate_skills = parse_skills(candidate_job.detected_skills)
        shared_skills = sorted(target_skills & candidate_skills)

        score_parts = compute_hybrid_score(
            embedding_score=float(embedding_score),
            target_skills=target_skills,
            candidate_skills=candidate_skills,
            same_category=same_category,
            same_seniority=same_seniority,
        )

        score = float(score_parts["final_score"])
        embedding_score_value = float(score_parts["embedding_score"])
        skill_overlap_score = float(score_parts["skill_overlap_score"])

        if any(map(_is_nan, [score, embedding_score_value, skill_overlap_score])):
            continue

        ranked.append(
            {
                "job_id": int(candidate_job.id),
                "title": str(candidate_job.title),
                "score": score,
                "embedding_score": embedding_score_value,
                "skill_overlap_score": skill_overlap_score,
                "shared_skills": shared_skills,
                "same_category": same_category,
                "same_seniority": same_seniority,
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:limit]


def _is_nan(value: float) -> bool:
    return value != value