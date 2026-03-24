RAG_EVAL_CASES = [
    {
        "question": "Which backend jobs require FastAPI and PostgreSQL?",
        "filters": {"category": "Backend"},
        "expected_keywords": ["fastapi", "postgresql", "backend"],
    },
    {
        "question": "What skills are common in junior analytics roles?",
        "filters": {"category": "Analytics", "seniority": "Junior"},
        "expected_keywords": ["sql", "python", "analytics", "reports"],
    },
    {
        "question": "Which ML jobs mention embeddings or transformers?",
        "filters": {"category": "ML"},
        "expected_keywords": ["embeddings", "transformers", "nlp"],
    },
    {
        "question": "Which data engineering roles mention ETL and SQL?",
        "filters": {"category": "Data"},
        "expected_keywords": ["etl", "sql", "pipelines"],
    },
]