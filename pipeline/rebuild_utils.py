import os


def artifacts_exist(paths: list[str]) -> bool:
    return all(os.path.exists(path) for path in paths)


def should_rebuild_from_dirty_count(*, dirty_count: int, artifact_paths: list[str]) -> bool:
    if not artifacts_exist(artifact_paths):
        return True
    return dirty_count > 0


def should_force_full_rebuild(full_rebuild: bool) -> bool:
    return bool(full_rebuild)