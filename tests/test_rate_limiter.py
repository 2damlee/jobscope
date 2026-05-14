import time
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api import rag as rag_module


def make_request(ip: str = "1.2.3.4", forwarded_for: str | None = None) -> MagicMock:
    """Build a minimal mock Request with the given IP/header."""
    req = MagicMock()
    req.client.host = ip
    req.headers = {"x-forwarded-for": forwarded_for} if forwarded_for else {}
    return req


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear the in-memory hit counter before and after every test."""
    rag_module._hits.clear()
    yield
    rag_module._hits.clear()
    

def test_requests_within_limit_pass(monkeypatch):
    monkeypatch.setattr(rag_module, "RAG_RATE_LIMIT_REQUESTS", 5)
    monkeypatch.setattr(rag_module, "RAG_RATE_LIMIT_WINDOW_SECONDS", 60)

    req = make_request()
    for _ in range(5):
        rag_module._check_rate_limit(req)  # should not raise


def test_exceeding_limit_raises_429(monkeypatch):
    monkeypatch.setattr(rag_module, "RAG_RATE_LIMIT_REQUESTS", 3)
    monkeypatch.setattr(rag_module, "RAG_RATE_LIMIT_WINDOW_SECONDS", 60)

    req = make_request()
    for _ in range(3):
        rag_module._check_rate_limit(req)

    with pytest.raises(HTTPException) as exc_info:
        rag_module._check_rate_limit(req)

    assert exc_info.value.status_code == 429
    assert "Too many" in exc_info.value.detail


def test_hits_outside_window_expire(monkeypatch):
    monkeypatch.setattr(rag_module, "RAG_RATE_LIMIT_REQUESTS", 2)
    monkeypatch.setattr(rag_module, "RAG_RATE_LIMIT_WINDOW_SECONDS", 1)

    req = make_request()

    # Fill up the limit
    for _ in range(2):
        rag_module._check_rate_limit(req)

    # Immediately blocked
    with pytest.raises(HTTPException) as exc_info:
        rag_module._check_rate_limit(req)
    assert exc_info.value.status_code == 429

    # Wait for window to expire
    time.sleep(1.1)

    # Should pass again — old hits purged
    rag_module._check_rate_limit(req)  # should not raise


def test_different_clients_have_independent_counters(monkeypatch):
    monkeypatch.setattr(rag_module, "RAG_RATE_LIMIT_REQUESTS", 2)
    monkeypatch.setattr(rag_module, "RAG_RATE_LIMIT_WINDOW_SECONDS", 60)

    client_a = make_request(ip="1.2.3.4")
    client_b = make_request(ip="9.9.9.9")

    # Client A hits the limit
    for _ in range(2):
        rag_module._check_rate_limit(client_a)

    with pytest.raises(HTTPException) as exc_info:
        rag_module._check_rate_limit(client_a)
    assert exc_info.value.status_code == 429

    # Client B is unaffected — different IP key
    rag_module._check_rate_limit(client_b)  # should not raise


def test_x_forwarded_for_is_used_as_key(monkeypatch):
    monkeypatch.setattr(rag_module, "RAG_RATE_LIMIT_REQUESTS", 1)
    monkeypatch.setattr(rag_module, "RAG_RATE_LIMIT_WINDOW_SECONDS", 60)

    mock_request = MagicMock()
    mock_request.headers = {"x-forwarded-for": "5.5.5.5, 10.0.0.1"}
    mock_request.client = None

    key = rag_module._client_key(mock_request)
    assert key == "5.5.5.5"
    

def test_falls_back_to_client_host_when_no_forwarded_header(monkeypatch):
    mock_request = MagicMock()
    mock_request.headers = {}
    mock_request.client.host = "192.168.1.1"

    key = rag_module._client_key(mock_request)
    assert key == "192.168.1.1"


def test_unknown_client_does_not_crash(monkeypatch):
    mock_request = MagicMock()
    mock_request.headers = {}
    mock_request.client = None

    key = rag_module._client_key(mock_request)
    assert key == "unknown"