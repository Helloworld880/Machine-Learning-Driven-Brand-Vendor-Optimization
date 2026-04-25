import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from config.settings import get_settings
from database.db import engine
from utils.redis_client import redis_client
from utils.security import hash_password


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
settings = get_settings()


RAW_FILE = Path("Data layer/vendors.csv")


def extract() -> pd.DataFrame:
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Source file not found: {RAW_FILE}")
    logger.info("Extracting raw data from %s", RAW_FILE)
    return pd.read_csv(RAW_FILE)


def transform(frame: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transforming %s rows", len(frame))
    data = frame.copy()
    data = data.rename(
        columns={
            "id": "id",
            "name": "name",
        }
    )
    for col in ["delivery_rate", "quality_score", "cost_efficiency", "actual_cost", "expected_cost"]:
        if col not in data.columns:
            data[col] = 0

    if "on_time_deliveries" not in data.columns:
        data["on_time_deliveries"] = 0
    if "total_deliveries" not in data.columns:
        data["total_deliveries"] = 1

    keep = [
        "id",
        "name",
        "category",
        "status",
        "delivery_rate",
        "quality_score",
        "cost_efficiency",
        "actual_cost",
        "expected_cost",
        "on_time_deliveries",
        "total_deliveries",
    ]
    for col in keep:
        if col not in data.columns:
            data[col] = None
    return data[keep]


def load(frame: pd.DataFrame) -> None:
    logger.info("Loading %s rows into PostgreSQL", len(frame))
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS vendors (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                status TEXT,
                delivery_rate DOUBLE PRECISION,
                quality_score DOUBLE PRECISION,
                cost_efficiency DOUBLE PRECISION,
                actual_cost DOUBLE PRECISION,
                expected_cost DOUBLE PRECISION,
                on_time_deliveries DOUBLE PRECISION,
                total_deliveries DOUBLE PRECISION
            )
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                role TEXT NOT NULL DEFAULT 'viewer',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'viewer'"))

        conn.execute(text("TRUNCATE TABLE vendors"))
        frame.to_sql("vendors", con=conn, if_exists="append", index=False)

        admin_hash = hash_password(settings.ADMIN_PASSWORD)
        conn.execute(
            text(
                """
                INSERT INTO users (username, password_hash, is_active, role)
                VALUES (:username, :password_hash, TRUE, :role)
                ON CONFLICT (username) DO UPDATE
                SET password_hash = EXCLUDED.password_hash,
                    is_active = TRUE,
                    role = EXCLUDED.role
                """
            ),
            {
                "username": settings.ADMIN_USERNAME,
                "password_hash": admin_hash,
                "role": settings.ADMIN_ROLE,
            },
        )
    logger.info("Load complete")


def invalidate_caches() -> None:
    try:
        r = redis_client.get_client()
        keys = list(r.scan_iter(match="vendors:performance:*", count=500))
        if keys:
            r.delete(*keys)
        logger.info("Invalidated %s vendor performance cache keys", len(keys))
    except Exception as exc:
        logger.error("Failed to invalidate Redis caches: %s", exc)


def run_pipeline() -> None:
    raw = extract()
    transformed = transform(raw)
    load(transformed)
    invalidate_caches()


if __name__ == "__main__":
    run_pipeline()
