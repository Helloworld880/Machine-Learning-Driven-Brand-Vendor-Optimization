import hashlib

from core_modules.auth import Authentication, _verify_password, hash_password


def test_hash_password_uses_pbkdf2_format():
    hashed = hash_password("secret123", iterations=1000)
    assert hashed.startswith("pbkdf2_sha256$")
    assert _verify_password(hashed, "secret123") is True
    assert _verify_password(hashed, "wrong") is False


def test_authentication_accepts_legacy_sha256_hash():
    legacy_hash = hashlib.sha256("admin123".encode()).hexdigest()

    class FakeDB:
        def get_user(self, username):
            if username == "admin":
                return {
                    "id": 1,
                    "username": "admin",
                    "password": legacy_hash,
                    "name": "Administrator",
                    "email": "admin@company.com",
                    "role": "admin",
                }
            return None

    auth = Authentication(db=FakeDB())
    user = auth.authenticate("admin", "admin123")
    assert user is not None
    assert user["username"] == "admin"
