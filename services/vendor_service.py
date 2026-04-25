import logging
import math
from io import StringIO

import pandas as pd

from database.queries import get_vendor_performance_page, get_vendors_page
from models.model import VendorRiskModel


logger = logging.getLogger(__name__)


class VendorService:
    def __init__(self) -> None:
        self.risk_model = VendorRiskModel()
        self.risk_model.load()

    @staticmethod
    def _calculate_metrics(frame: pd.DataFrame) -> pd.DataFrame:
        data = frame.copy()
        data["on_time_rate"] = (
            (data["on_time_deliveries"].fillna(0) / data["total_deliveries"].replace(0, pd.NA))
            .fillna(0)
            .mul(100)
            .round(2)
        )
        data["cost_variance"] = (data["actual_cost"].fillna(0) - data["expected_cost"].fillna(0)).round(2)
        data["reliability"] = ((data["on_time_rate"] * 0.6) + (data["quality_score"].fillna(0) * 0.4)).round(2)
        data["performance_score"] = (
            (data["delivery_rate"].fillna(0) * 0.4)
            + (data["quality_score"].fillna(0) * 0.3)
            + (data["cost_efficiency"].fillna(0) * 0.3)
        ).round(2)
        return data

    def get_vendor_kpis(self, page: int, limit: int) -> tuple[pd.DataFrame, dict]:
        source, total_records = get_vendors_page(page=page, limit=limit)
        if source.empty:
            return source, {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "total_pages": math.ceil(total_records / limit) if limit else 0,
            }

        enriched = self._calculate_metrics(source)
        enriched["risk_prediction"] = self.risk_model.predict_risk(enriched)
        pagination = {
            "page": page,
            "limit": limit,
            "total_records": total_records,
            "total_pages": math.ceil(total_records / limit) if limit else 0,
        }
        return enriched, pagination

    def get_vendor_performance(self, page: int, limit: int) -> tuple[pd.DataFrame, dict]:
        data, total_records = get_vendor_performance_page(page=page, limit=limit)
        if data.empty:
            return data, {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "total_pages": math.ceil(total_records / limit) if limit else 0,
            }

        leaderboard = data.copy()
        leaderboard["alert"] = leaderboard["performance_score"].apply(
            lambda score: "low_performance_alert" if score < 60 else "normal"
        )
        pagination = {
            "page": page,
            "limit": limit,
            "total_records": total_records,
            "total_pages": math.ceil(total_records / limit) if limit else 0,
        }
        return leaderboard, pagination

    def export_vendor_performance_csv(self, page: int, limit: int) -> str:
        perf, _ = self.get_vendor_performance(page=page, limit=limit)
        buffer = StringIO()
        perf.to_csv(buffer, index=False)
        return buffer.getvalue()
