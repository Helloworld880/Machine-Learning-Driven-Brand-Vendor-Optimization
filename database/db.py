import logging

from sqlalchemy import create_engine
from sqlalchemy import text

from config.settings import get_settings


settings = get_settings()
logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL, future=True, pool_pre_ping=True)


def initialize_database() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
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
        )
        conn.execute(
            text(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'viewer'
                """
            )
        )
        conn.execute(
            text(
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
        )
