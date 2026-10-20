import pytest
from fastapi.testclient import TestClient
import config

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "t.db"))
    import main
    main.db.init_db()
    return TestClient(main.app)

H = {"X-Reviewer-Key": config.REVIEWER_API_KEY}
n = iter(range(10000))
def post(c, amount, name="Asha"):
    return c.post("/applications", json={"name": name, "reference": f"R{next(n)}", "amount": amount})

@pytest.mark.parametrize("amount,status", [(500,"AUTO_ACCEPTED"),(999,"AUTO_ACCEPTED"),(1000,"PENDING_HUMAN_REVIEW"),
    (5000,"PENDING_HUMAN_REVIEW"),(10000,"PENDING_HUMAN_REVIEW"),(10001,"AUTO_APPROVAL_PATH")])
def test_routes(client, amount, status):
    assert post(client, amount).json()["status"] == status

@pytest.mark.parametrize("amount", [0, -5, "abc", None])
def test_invalid(client, amount):
    assert post(client, amount).status_code == 422

def test_duplicate_reference(client):
    body = {"name": "A", "reference": "DUP", "amount": 500}
    assert client.post("/applications", json=body).status_code == 201
    assert client.post("/applications", json=body).status_code == 409

def test_monitoring_mismatch_blocks(client, monkeypatch):
    from agents import approval_agent
    monkeypatch.setattr(approval_agent, "decide", lambda a: {"route": "AUTO_APPROVE", "reason": "bad"})
    assert post(client, 500).json()["status"] == "MONITORING_ERROR"

def test_human_approve_and_replay(client):
    i = post(client, 5000).json()["id"]
    r = {"reviewer": "Rev", "decision": "approve"}
    assert client.post(f"/review/{i}", json=r, headers=H).json()["status"] == "APPROVED"
    assert client.post(f"/review/{i}", json=r, headers=H).status_code == 409
    assert client.get(f"/applications/{i}").json()["status"] == "APPROVED"

def test_human_reject_needs_reason(client):
    i = post(client, 5000).json()["id"]
    assert client.post(f"/review/{i}", json={"reviewer": "Rev", "decision": "reject"}, headers=H).status_code == 422
    r = client.post(f"/review/{i}", json={"reviewer": "Rev", "decision": "reject", "reason": "Incomplete"}, headers=H)
    assert r.json()["status"] == "REJECTED"

def test_unauthorized(client):
    i = post(client, 5000).json()["id"]
    body = {"reviewer": "Rev", "decision": "approve"}
    assert client.post(f"/review/{i}", json=body).status_code == 401
    assert client.post(f"/review/{i}", json=body, headers={"X-Reviewer-Key": "x"}).status_code == 403
    assert client.get("/review/pending").status_code == 401

def test_self_review_blocked_and_no_review_of_auto(client):
    i = post(client, 5000, name="Sam").json()["id"]
    assert client.post(f"/review/{i}", json={"reviewer": "sam", "decision": "approve"}, headers=H).status_code == 403
    j = post(client, 500).json()["id"]
    assert client.post(f"/review/{j}", json={"reviewer": "Rev", "decision": "approve"}, headers=H).status_code == 409
