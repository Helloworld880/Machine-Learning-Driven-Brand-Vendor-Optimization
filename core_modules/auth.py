
import hashlib
import jwt
import datetime
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

SECRET_KEY = "change_this_in_production_secret_key_2024"
JWT_EXPIRY_HOURS = 24


class Authentication:
    def __init__(self, db=None):
        self.db = db
        self.secret_key = SECRET_KEY

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user against DB; fallback to admin hardcode for demo."""
        pw_hash = self._hash_password(password)

        # Try DB lookup
        if self.db:
            try:
                user = self.db.get_user(username)
                if user and user["password"] == pw_hash:
                    return {k: user[k] for k in ("id", "username", "name", "email", "role")}
            except Exception as e:
                logger.warning(f"DB auth error: {e}")

        # Hardcoded fallback (demo only)
        if username == "" and password == "":
            return {"id": 1, "username": "admin", "name": "Administrator",
                    "email": "admin@company.com", "role": "admin"}
        return None

    def generate_token(self, user_id: int) -> str:
        payload = {
            "user_id": user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
            "iat": datetime.datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[Dict]:
        try:
            return jwt.decode(token, self.secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT: {e}")
        return None