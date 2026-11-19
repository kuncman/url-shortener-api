import pytest
from fastapi.testclient import TestClient

import app.main as main


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", str(tmp_path / "test.db"))
    with TestClient(main.app) as c:
        yield c


def test_create_and_redirect(client):
    r = client.post("/links", json={"url": "https://example.com/page"})
    assert r.status_code == 201
    code = r.json()["code"]
    assert len(code) == main.CODE_LENGTH

    r = client.get(f"/{code}", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "https://example.com/page"


def test_click_counter(client):
    code = client.post("/links", json={"url": "https://example.com"}).json()["code"]
    for _ in range(3):
        client.get(f"/{code}", follow_redirects=False)
    assert client.get(f"/links/{code}").json()["clicks"] == 3


def test_custom_code_conflict(client):
    body = {"url": "https://example.com", "custom_code": "my-link"}
    assert client.post("/links", json=body).status_code == 201
    assert client.post("/links", json=body).status_code == 409


def test_invalid_url_rejected(client):
    assert client.post("/links", json={"url": "not a url"}).status_code == 422


def test_bad_custom_code_rejected(client):
    r = client.post("/links", json={"url": "https://example.com", "custom_code": "a b"})
    assert r.status_code == 422


def test_unknown_code_404(client):
    assert client.get("/nope123", follow_redirects=False).status_code == 404


def test_delete(client):
    code = client.post("/links", json={"url": "https://example.com"}).json()["code"]
    assert client.delete(f"/links/{code}").status_code == 204
    assert client.get(f"/links/{code}").status_code == 404
