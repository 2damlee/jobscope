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

    def fake_list_recommendations(db, job_id, limit=5):
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
        "pipeline.evaluate_recommendations.list_recommendations",
        fake_list_recommendations,
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

