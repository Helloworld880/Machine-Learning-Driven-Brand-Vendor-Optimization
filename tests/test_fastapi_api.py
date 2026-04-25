import pandas as pd
from fastapi.testclient import TestClient

import api.main as api_main


class StubVendorService:
    def get_vendor_kpis(self, page, limit):
        return pd.DataFrame([{"vendor_id": 1, "vendor_name": "Alpha", "performance_score": 82.5}]), {
            "page": page,
            "limit": limit,
            "total_records": 1,
            "total_pages": 1,
        }

    def get_vendor_performance(self, page, limit):
        return pd.DataFrame([{"vendor_id": 1, "vendor_name": "Alpha", "performance_score": 82.5, "rank": 1, "alert": "normal"}]), {
            "page": page,
            "limit": limit,
            "total_records": 1,
            "total_pages": 1,
        }

    def export_vendor_performance_csv(self, page, limit):
        return "vendor_id,vendor_name\n1,Alpha\n"


class FakeRedis:
    def __init__(self):
        self.store = {}

    def ping(self):
        return True

    def eval(self, script, key_count, key, ttl):
        self.store[key] = int(self.store.get(key, 0)) + 1
        return self.store[key]

    def exists(self, key):
        return 1 if key in self.store else 0

    def setex(self, key, ttl, value):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key)


def _client(monkeypatch):
    monkeypatch.setattr(api_main, "initialize_database", lambda: None)
    monkeypatch.setattr(api_main, "vendor_service", StubVendorService())
    monkeypatch.setattr(api_main, "_redis_safe_client", lambda: FakeRedis())
    return TestClient(api_main.app)


def _token_for(role: str = "viewer"):
    return api_main._create_access_token(subject="admin", role=role)


def test_login_success(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(
        api_main,
        "get_user_by_username",
        lambda username: {"username": username, "password_hash": "x", "is_active": True, "role": "admin"},
    )
    monkeypatch.setattr(api_main, "verify_password", lambda password, password_hash: True)

    res = client.post("/api/v1/login", data={"username": "admin", "password": "secret"})
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_login_failure(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(api_main, "get_user_by_username", lambda username: None)
    res = client.post("/api/v1/login", data={"username": "admin", "password": "bad"})
    assert res.status_code == 401


def test_vendors_protected(monkeypatch):
    client = _client(monkeypatch)
    res = client.get("/api/v1/vendors")
    assert res.status_code == 401

    token = _token_for(role="viewer")
    res = client.get("/api/v1/vendors?page=1&limit=20", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert isinstance(res.json().get("data"), list)


def test_export_requires_admin(monkeypatch):
    client = _client(monkeypatch)
    viewer = _token_for(role="viewer")
    res = client.get("/api/v1/vendors/performance/export", headers={"Authorization": f"Bearer {viewer}"})
    assert res.status_code == 403

    admin = _token_for(role="admin")
    res = client.get("/api/v1/vendors/performance/export", headers={"Authorization": f"Bearer {admin}"})
    assert res.status_code == 200
    assert "vendor_id" in res.text


def test_refresh_token(monkeypatch):
    client = _client(monkeypatch)
    refresh = api_main._create_refresh_token(subject="admin", role="admin")
    res = client.post("/api/v1/refresh", json={"refresh_token": refresh})
    assert res.status_code == 200
    assert "access_token" in res.json()
