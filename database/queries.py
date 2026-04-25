import pandas as pd
from sqlalchemy import text

from database.db import engine


def get_vendors_page(page: int, limit: int) -> tuple[pd.DataFrame, int]:
    offset = (page - 1) * limit
    data_query = text(
        """
        SELECT
            v.id AS vendor_id,
            v.name AS vendor_name,
            v.category,
            v.status,
            v.delivery_rate,
            v.quality_score,
            v.cost_efficiency,
            v.actual_cost,
            v.expected_cost,
            v.on_time_deliveries,
            v.total_deliveries
        FROM vendors v
        ORDER BY v.id
        LIMIT :limit OFFSET :offset
        """
    )
    count_query = text("SELECT COUNT(*) AS total_records FROM vendors")
    with engine.begin() as conn:
        frame = pd.read_sql(data_query, con=conn, params={"limit": limit, "offset": offset})
        total = conn.execute(count_query).scalar_one()
    return frame, int(total)


def get_vendor_performance_page(page: int, limit: int) -> tuple[pd.DataFrame, int]:
    offset = (page - 1) * limit
    query = text(
        """
        WITH scored AS (
            SELECT
                v.id AS vendor_id,
                v.name AS vendor_name,
                v.category,
                v.status,
                v.delivery_rate,
                v.quality_score,
                v.cost_efficiency,
                v.actual_cost,
                v.expected_cost,
                v.on_time_deliveries,
                v.total_deliveries,
                (v.delivery_rate * 0.4 + v.quality_score * 0.3 + v.cost_efficiency * 0.3) AS performance_score,
                CASE
                    WHEN v.total_deliveries = 0 THEN 0
                    ELSE (v.on_time_deliveries / v.total_deliveries) * 100
                END AS on_time_rate,
                (v.actual_cost - v.expected_cost) AS cost_variance
            FROM vendors v
        )
        SELECT
            *,
            (on_time_rate * 0.6 + quality_score * 0.4) AS reliability,
            ROW_NUMBER() OVER (ORDER BY performance_score DESC, vendor_id ASC) AS rank
        FROM scored
        ORDER BY performance_score DESC, vendor_id ASC
        LIMIT :limit OFFSET :offset
        """
    )
    count_query = text("SELECT COUNT(*) AS total_records FROM vendors")
    with engine.begin() as conn:
        frame = pd.read_sql(query, con=conn, params={"limit": limit, "offset": offset})
        total = conn.execute(count_query).scalar_one()
    return frame, int(total)


def get_user_by_username(username: str) -> dict | None:
    query = text(
        """
        SELECT username, password_hash, is_active, role
        FROM users
        WHERE username = :username
        LIMIT 1
        """
    )
    with engine.begin() as conn:
        row = conn.execute(query, {"username": username}).mappings().first()
    return dict(row) if row else None
