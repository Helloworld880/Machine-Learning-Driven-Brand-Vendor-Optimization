import logging

import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request

from api._compat import jwt_required
from core_modules.analytics import AnalyticsEngine
from core_modules.database import DatabaseManager
from enhancements.report_generator import ReportGenerator


performance_bp = Blueprint("performance", __name__)
db_manager = DatabaseManager()
analytics_engine = AnalyticsEngine(db_manager)
logger = logging.getLogger(__name__)


def _records(df):
    if df is None or df.empty:
        return []
    return df.where(df.notna(), None).to_dict("records")


def _segment_vendors(vendors: pd.DataFrame) -> pd.DataFrame:
    if vendors.empty or "avg_performance" not in vendors.columns:
        return pd.DataFrame()

    segments = vendors[["vendor_id", "name", "avg_performance", "risk_level", "category"]].copy()
    ranked = segments["avg_performance"].rank(method="first")
    try:
        segments["segment"] = pd.qcut(ranked, q=3, labels=["Watchlist", "Stable", "Top Tier"])
    except ValueError:
        segments["segment"] = "Stable"
    segments = segments.rename(columns={"avg_performance": "performance_score"})
    segments["risk_score"] = segments["risk_level"].map({"Low": 20, "Medium": 50, "High": 80}).fillna(0)
    return segments


@performance_bp.route("/api/performance", methods=["GET"])
@jwt_required()
def get_performance_data():
    try:
        vendor_id = request.args.get("vendor_id")
        detailed = request.args.get("detailed", "false").lower() == "true"
        performance = db_manager.get_performance_data()

        if vendor_id:
            vendor_history = performance[performance["vendor_id"] == int(vendor_id)].sort_values("metric_date")
            payload = {"performance_history": _records(vendor_history)}
            if detailed and not vendor_history.empty:
                payload["summary"] = {
                    "latest_score": float(vendor_history.iloc[0]["overall_score"]),
                    "average_score": float(vendor_history["overall_score"].mean()),
                    "latest_quality": float(vendor_history.iloc[0]["quality_score"]),
                }
            return jsonify({"success": True, "data": payload}), 200

        vendors = db_manager.get_vendors_with_performance()
        trends = db_manager.get_performance_trends()
        segments = _segment_vendors(vendors)

        return jsonify(
            {
                "success": True,
                "data": {
                    "average_performance": float(vendors["avg_performance"].mean()) if not vendors.empty else 0.0,
                    "trends": _records(trends),
                    "distribution": _records(vendors[["vendor_id", "name", "avg_performance"]]) if not vendors.empty else [],
                    "segments": _records(segments),
                },
            }
        ), 200
    except Exception as exc:
        logger.error("Error fetching performance data: %s", exc)
        return jsonify({"success": False, "message": "Failed to fetch performance data"}), 500


@performance_bp.route("/api/performance/alerts", methods=["GET"])
@jwt_required()
def get_performance_alerts():
    try:
        return jsonify({"success": True, "data": analytics_engine.get_recent_alerts()}), 200
    except Exception as exc:
        logger.error("Error fetching performance alerts: %s", exc)
        return jsonify({"success": False, "message": "Failed to fetch performance alerts"}), 500


@performance_bp.route("/api/performance/benchmarks", methods=["GET"])
@jwt_required()
def get_performance_benchmarks():
    try:
        vendors = db_manager.get_vendors_with_performance()
        if vendors.empty:
            return jsonify({"success": True, "data": {"industry_comparison": [], "peer_comparison": []}}), 200

        category_scores = (
            vendors.groupby("category", as_index=False)["avg_performance"]
            .mean()
            .rename(columns={"avg_performance": "average_performance"})
        )
        top_peers = vendors.sort_values("avg_performance", ascending=False).head(10)

        return jsonify(
            {
                "success": True,
                "data": {
                    "industry_comparison": _records(category_scores),
                    "peer_comparison": _records(top_peers[["vendor_id", "name", "category", "avg_performance", "risk_level"]]),
                    "improvement_opportunities": analytics_engine.get_recent_alerts(),
                },
            }
        ), 200
    except Exception as exc:
        logger.error("Error fetching performance benchmarks: %s", exc)
        return jsonify({"success": False, "message": "Failed to fetch performance benchmarks"}), 500


@performance_bp.route("/api/performance/predictions", methods=["GET"])
@jwt_required()
def get_performance_predictions():
    try:
        vendor_id = request.args.get("vendor_id")
        trends = db_manager.get_performance_trends()
        risks = db_manager.get_risk_data()

        if vendor_id:
            performance = db_manager.get_performance_data()
            vendor_history = performance[performance["vendor_id"] == int(vendor_id)].sort_values("metric_date")
            forecast = vendor_history[["metric_date", "overall_score"]].tail(6)
            return jsonify(
                {
                    "success": True,
                    "data": {
                        "attrition_risk": _records(risks[risks["vendor_id"] == int(vendor_id)][["vendor_id", "vendor_name", "overall_risk", "risk_level"]]),
                        "performance_forecast": _records(forecast),
                    },
                }
            ), 200

        return jsonify(
            {
                "success": True,
                "data": _records(risks[["vendor_id", "vendor_name", "overall_risk", "risk_level"]]) if not risks.empty else [],
            }
        ), 200
    except Exception as exc:
        logger.error("Error fetching performance predictions: %s", exc)
        return jsonify({"success": False, "message": "Failed to fetch performance predictions"}), 500


@performance_bp.route("/api/performance/outliers", methods=["GET"])
@jwt_required()
def get_performance_outliers():
    try:
        metric = request.args.get("metric", "overall_score")
        threshold = float(request.args.get("threshold", 2.0))
        performance = db_manager.get_performance_data()
        if performance.empty or metric not in performance.columns:
            return jsonify({"success": True, "data": []}), 200

        values = pd.to_numeric(performance[metric], errors="coerce")
        z_scores = np.abs((values - values.mean()) / (values.std(ddof=0) + 1e-9))
        outliers = performance.loc[z_scores > threshold, ["vendor_id", "vendor_name", "metric_date", metric]].copy()
        outliers["z_score"] = z_scores[z_scores > threshold]

        return jsonify({"success": True, "data": _records(outliers)}), 200
    except Exception as exc:
        logger.error("Error identifying outliers: %s", exc)
        return jsonify({"success": False, "message": "Failed to identify outliers"}), 500


@performance_bp.route("/api/performance/correlations", methods=["GET"])
@jwt_required()
def get_performance_correlations():
    try:
        performance = db_manager.get_performance_data()
        numeric = performance.select_dtypes(include=["number"])
        if numeric.empty:
            return jsonify({"success": True, "data": {}}), 200
        return jsonify({"success": True, "data": numeric.corr().round(3).to_dict()}), 200
    except Exception as exc:
        logger.error("Error calculating correlations: %s", exc)
        return jsonify({"success": False, "message": "Failed to calculate correlations"}), 500


@performance_bp.route("/api/performance/trends", methods=["GET"])
@jwt_required()
def get_performance_trends():
    try:
        trend_type = request.args.get("type", "overall")
        trends_data = db_manager.get_performance_trends()
        if trend_type == "category":
            vendors = db_manager.get_vendors_with_performance()
            trends_data = vendors.groupby("category", as_index=False)["avg_performance"].mean()
        return jsonify({"success": True, "data": _records(trends_data)}), 200
    except Exception as exc:
        logger.error("Error fetching performance trends: %s", exc)
        return jsonify({"success": False, "message": "Failed to fetch performance trends"}), 500


@performance_bp.route("/api/performance/segments", methods=["GET"])
@jwt_required()
def get_performance_segments():
    try:
        vendors = db_manager.get_vendors_with_performance()
        segments = _segment_vendors(vendors)
        if segments.empty:
            return jsonify({"success": True, "data": {"segments": [], "statistics": {}}}), 200

        stats = (
            segments.groupby("segment")
            .agg(
                vendor_count=("vendor_id", "count"),
                average_performance=("performance_score", "mean"),
                average_risk=("risk_score", "mean"),
            )
            .round(2)
            .reset_index()
        )
        return jsonify({"success": True, "data": {"segments": _records(segments), "statistics": _records(stats)}}), 200
    except Exception as exc:
        logger.error("Error calculating segments: %s", exc)
        return jsonify({"success": False, "message": "Failed to calculate segments"}), 500


@performance_bp.route("/api/performance/reports", methods=["POST"])
@jwt_required()
def generate_performance_report():
    try:
        data = request.get_json() or {}
        report_format = data.get("format", "pdf")
        report_type = data.get("type", "Vendor Performance")

        generator = ReportGenerator(db_manager)
        report_path = generator.generate_report(report_type, report_format)

        return jsonify({"success": True, "message": "Report generated successfully", "report_path": report_path}), 200
    except Exception as exc:
        logger.error("Error generating performance report: %s", exc)
        return jsonify({"success": False, "message": "Failed to generate performance report"}), 500
