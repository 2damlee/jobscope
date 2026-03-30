from pipeline.rebuild_utils import artifacts_exist, should_rebuild_from_dirty_count


def test_artifacts_exist_true(monkeypatch):
    monkeypatch.setattr("pipeline.rebuild_utils.os.path.exists", lambda _: True)
    assert artifacts_exist(["a", "b", "c"]) is True


def test_artifacts_exist_false(monkeypatch):
    monkeypatch.setattr("pipeline.rebuild_utils.os.path.exists", lambda path: path != "b")
    assert artifacts_exist(["a", "b", "c"]) is False


def test_should_rebuild_when_artifact_missing(monkeypatch):
    monkeypatch.setattr("pipeline.rebuild_utils.os.path.exists", lambda _: False)
    assert should_rebuild_from_dirty_count(dirty_count=0, artifact_paths=["a", "b"]) is True


def test_should_rebuild_when_dirty_count_positive(monkeypatch):
    monkeypatch.setattr("pipeline.rebuild_utils.os.path.exists", lambda _: True)
    assert should_rebuild_from_dirty_count(dirty_count=2, artifact_paths=["a", "b"]) is True


def test_should_not_rebuild_when_artifacts_exist_and_dirty_count_zero(monkeypatch):
    monkeypatch.setattr("pipeline.rebuild_utils.os.path.exists", lambda _: True)
    assert should_rebuild_from_dirty_count(dirty_count=0, artifact_paths=["a", "b"]) is False