"""API smoke tests: run a campaign over HTTP and read it back."""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/redline_api_test.db"

_DB = "/tmp/redline_api_test.db"
if os.path.exists(_DB):
    os.remove(_DB)

from fastapi.testclient import TestClient  # noqa: E402

from redline.api.app import app  # noqa: E402

client = TestClient(app)

# basics pack is 10 probes: 3+3+3+4+5+3+3+3+3+3 = 33 attempts
EXPECTED_ATTEMPTS = 33


def test_create_campaign():
    r = client.post(
        "/campaigns",
        json={"target": "hardened", "pack": "basics", "name": "api-test"},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["verdict_counts"].get("pass") == EXPECTED_ATTEMPTS
    assert len(data["attempts"]) == EXPECTED_ATTEMPTS
    assert data["attempts"][0]["messages"]
    return data["id"]


def test_list_and_detail():
    cid = test_create_campaign()
    r = client.get("/campaigns")
    assert r.status_code == 200
    assert any(c["id"] == cid for c in r.json())
    r = client.get(f"/campaigns/{cid}")
    assert r.status_code == 200
    assert r.json()["name"] == "api-test"


def test_bad_target_rejected():
    r = client.post("/campaigns", json={"target": "nope", "pack": "basics"})
    assert r.status_code == 400


def test_missing_campaign_404():
    r = client.get("/campaigns/999999")
    assert r.status_code == 404
