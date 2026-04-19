import json

from app.config import PROCESSED_DIR, ensure_data_dirs
from app.db import SessionLocal
from app.models import Job
from app.recommendation import parse_skills
from app.services.recommend_service import list_recommendations_for_offline_eval
from app.time_utils import utcnow_naive


def evaluate_recommendations(limit: int = 5, sample_size: int = 20) -> dict:
    db = SessionLocal()

    try:
        jobs = (
            db.query(Job)
            .filter(Job.detected_skills.isnot(None))
            .all()
        )[:sample_size]

        evaluated_jobs = 0
        jobs_with_recommendations = 0
        jobs_with_shared_skills = 0
        total_recommendations = 0
        case_results = []

        for job in jobs:
            target_skills = parse_skills(job.detected_skills)
            if not target_skills:
                continue

            recommendations = list_recommendations_for_offline_eval(
                db=db,
                job_id=job.id,
                limit=limit,
            )

            evaluated_jobs += 1

            if recommendations:
                jobs_with_recommendations += 1

            shared_skill_recommendations = sum(
                1 for item in recommendations if item["shared_skills"]
            )
            if shared_skill_recommendations > 0:
                jobs_with_shared_skills += 1

            total_recommendations += len(recommendations)

            case_results.append(
                {
                    "job_id": job.id,
                    "target_title": job.title,
                    "target_skill_count": len(target_skills),
                    "recommendation_count": len(recommendations),
                    "shared_skill_recommendations": shared_skill_recommendations,
                }
            )

        summary = {
            "evaluated_jobs": evaluated_jobs,
            "jobs_with_recommendations": jobs_with_recommendations,
            "jobs_with_shared_skills": jobs_with_shared_skills,
            "avg_recommendations_per_job": (
                round(total_recommendations / evaluated_jobs, 3)
                if evaluated_jobs
                else 0.0
            ),
        }

        ensure_data_dirs()
        output_path = PROCESSED_DIR / "recommendation_eval_results.json"

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at": utcnow_naive().isoformat(),
                    "summary": summary,
                    "cases": case_results,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        return {
            "summary": summary,
            "output_path": str(output_path),
        }
    finally:
        db.close()


if __name__ == "__main__":
    result = evaluate_recommendations()
    print(json.dumps(result, ensure_ascii=False, indent=2))