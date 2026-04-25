import re

import bcrypt


PASSWORD_POLICY = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{12,}$")


def validate_password_strength(password: str) -> None:
    if not PASSWORD_POLICY.match(password):
        raise ValueError("Password must be at least 12 chars with uppercase, lowercase, and number.")


def hash_password(password: str) -> str:
    validate_password_strength(password)
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
