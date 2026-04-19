from pipeline.rebuild_utils import artifacts_exist, should_rebuild_from_dirty_count


def test_artifacts_exist_returns_false_when_missing(tmp_path):
    paths = [
        str(tmp_path / "a.json"),
        str(tmp_path / "b.npy"),
    ]
    assert artifacts_exist(paths) is False


def test_artifacts_exist_returns_true_when_all_present(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.npy"
    a.write_text("{}", encoding="utf-8")
    b.write_text("x", encoding="utf-8")

    assert artifacts_exist([str(a), str(b)]) is True


def test_should_rebuild_when_artifacts_missing_even_if_no_dirty_jobs(tmp_path):
    paths = [
        str(tmp_path / "missing_a.json"),
        str(tmp_path / "missing_b.npy"),
    ]
    assert should_rebuild_from_dirty_count(dirty_count=0, artifact_paths=paths) is True


def test_should_not_rebuild_when_no_dirty_jobs_and_artifacts_exist(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.npy"
    a.write_text("{}", encoding="utf-8")
    b.write_text("x", encoding="utf-8")

    assert should_rebuild_from_dirty_count(
        dirty_count=0,
        artifact_paths=[str(a), str(b)],
    ) is False


def test_should_rebuild_when_dirty_jobs_exist_and_artifacts_exist(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.npy"
    a.write_text("{}", encoding="utf-8")
    b.write_text("x", encoding="utf-8")

    assert should_rebuild_from_dirty_count(
        dirty_count=3,
        artifact_paths=[str(a), str(b)],
    ) is True