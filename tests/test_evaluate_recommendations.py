from pipeline.evaluate_recommendations import evaluate_recommendations


class FakeJob:
    def __init__(self, job_id, title, detected_skills):
        self.id = job_id
        self.title = title
        self.detected_skills = detected_skills


class FakeQuery:
    def __init__(self, jobs):
        self.jobs = jobs

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self.jobs


class FakeSession:
    def __init__(self, jobs):
        self.jobs = jobs

    def query(self, model):
        return FakeQuery(self.jobs)

    def close(self):
        pass


def test_evaluate_recommendations_summarizes_results(monkeypatch, tmp_path):
    fake_jobs = [
        FakeJob(1, "Backend Engineer", "Python,FastAPI,SQL"),
        FakeJob(2, "Data Engineer", "Python,Airflow,SQL"),
    ]

    def fake_session_local():
        return FakeSession(fake_jobs)

    def fake_list_recommendations_for_offline_eval(
        db,
        job_id,
        limit=5,
        same_category_only=False,
        min_shared_skills=0,
        min_embedding_score=None,
    ):
        if job_id == 1:
            return [
                {"shared_skills": ["Python", "SQL"]},
                {"shared_skills": []},
            ]
        return [
            {"shared_skills": ["Python"]},
        ]

    monkeypatch.setattr(
        "pipeline.evaluate_recommendations.SessionLocal",
        fake_session_local,
    )
    monkeypatch.setattr(
        "pipeline.evaluate_recommendations.list_recommendations_for_offline_eval",
        fake_list_recommendations_for_offline_eval,
    )
    monkeypatch.setattr(
        "pipeline.evaluate_recommendations.PROCESSED_DIR",
        tmp_path,
    )

    result = evaluate_recommendations(limit=5, sample_size=10)

    summary = result["summary"]

    assert summary["evaluated_jobs"] == 2
    assert summary["jobs_with_recommendations"] == 2
    assert summary["jobs_with_shared_skills"] == 2
    assert summary["avg_recommendations_per_job"] == 1.5

def test_eval_uses_offline_function_with_matching_signature():
    """Guard test: the eval script must call the offline variant, and the call
    site must match its real signature. A mock with the wrong signature hid a
    TypeError here once — this test binds the real function's signature to the
    arguments the eval script uses, without touching the database.
    """
    import inspect

    from app.services import recommend_service
    from pipeline import evaluate_recommendations as eval_module

    # The eval module must import the offline variant, not the request-bound one.
    assert (
        eval_module.list_recommendations_for_offline_eval
        is recommend_service.list_recommendations_for_offline_eval
    )

    # Binding must succeed with the exact argument shape used in the eval loop.
    sig = inspect.signature(recommend_service.list_recommendations_for_offline_eval)
    sig.bind(object(), 1, limit=5)