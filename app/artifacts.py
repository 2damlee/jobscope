from pathlib import Path

from app.config import ARTIFACT_PATHS


def artifact_status() -> dict:
    items = []
    missing = []

    for path in ARTIFACT_PATHS:
        path_obj = Path(path)
        exists = path_obj.exists()

        items.append(
            {
                "name": path_obj.name,
                "path": str(path_obj),
                "exists": exists,
            }
        )

        if not exists:
            missing.append(str(path_obj))

    return {
        "ready": len(missing) == 0,
        "missing_count": len(missing),
        "missing": missing,
        "artifacts": items,
    }