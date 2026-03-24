from app.recommendation import parse_skills, jaccard_similarity, compute_hybrid_score


def test_parse_skills():
    assert parse_skills("python,sql,docker") == {"python", "sql", "docker"}
    assert parse_skills(None) == set()
    assert parse_skills("") == set()


def test_jaccard_similarity():
    a = {"python", "sql", "docker"}
    b = {"python", "sql"}
    assert round(jaccard_similarity(a, b), 4) == round(2 / 3, 4)


def test_compute_hybrid_score_prefers_matching_metadata():
    base = compute_hybrid_score(
        embedding_score=0.8,
        target_skills={"python", "sql"},
        candidate_skills={"python", "sql"},
        same_category=True,
        same_seniority=True,
    )

    weaker = compute_hybrid_score(
        embedding_score=0.8,
        target_skills={"python", "sql"},
        candidate_skills={"python"},
        same_category=False,
        same_seniority=False,
    )

    assert base["final_score"] > weaker["final_score"]
    