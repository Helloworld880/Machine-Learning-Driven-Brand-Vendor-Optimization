import csv
import logging
import sqlite3
from io import StringIO

from flask import Blueprint, jsonify, request

from api._compat import jwt_required
from core_modules.database import DatabaseManager


vendors_bp = Blueprint("vendors", __name__)
db_manager = DatabaseManager()
logger = logging.getLogger(__name__)


def _records(df):
    if df is None or df.empty:
        return []
    return df.where(df.notna(), None).to_dict("records")


@vendors_bp.route("/api/vendors", methods=["GET"])
@jwt_required()
def get_vendors():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        category = request.args.get("category")
        status = request.args.get("status")
        risk_level = request.args.get("risk_level")
        search = request.args.get("search", "").strip().lower()

        vendors = db_manager.get_vendors_with_performance()
        if category:
            categories = {item.strip() for item in category.split(",")}
            vendors = vendors[vendors["category"].isin(categories)]
        if status:
            vendors = vendors[vendors["status"].str.lower() == status.lower()]
        if risk_level:
            vendors = vendors[vendors["risk_level"].str.lower() == risk_level.lower()]
        if search:
            vendors = vendors[vendors["name"].str.lower().str.contains(search, na=False)]

        total_vendors = len(vendors)
        start_idx = max(page - 1, 0) * per_page
        paginated_vendors = vendors.iloc[start_idx:start_idx + per_page]

        return jsonify(
            {
                "success": True,
                "data": _records(paginated_vendors),
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total_vendors,
                    "total_pages": (total_vendors + per_page - 1) // per_page,
                },
            }
        ), 200
    except Exception as exc:
        logger.error("Error fetching vendors: %s", exc)
        return jsonify({"success": False, "message": "Failed to fetch vendors"}), 500


@vendors_bp.route("/api/vendors/<int:vendor_id>", methods=["GET"])
@jwt_required()
def get_vendor(vendor_id):
    try:
        vendors = db_manager.get_vendors_with_performance()
        match = vendors[vendors["vendor_id"] == vendor_id]
        if match.empty:
            return jsonify({"success": False, "message": "Vendor not found"}), 404

        vendor = match.iloc[0].to_dict()
        performance_history = db_manager.get_performance_data()
        performance_history = performance_history[performance_history["vendor_id"] == vendor_id]

        financial_data = db_manager.get_financial_data()
        financial_data = financial_data[financial_data["vendor_id"] == vendor_id]

        risk_assessments = db_manager.get_risk_data()
        risk_assessments = risk_assessments[risk_assessments["vendor_id"] == vendor_id]

        return jsonify(
            {
                "success": True,
                "data": {
                    "vendor": vendor,
                    "performance_history": _records(performance_history),
                    "financial_data": _records(financial_data),
                    "risk_assessments": _records(risk_assessments),
                },
            }
        ), 200
    except Exception as exc:
        logger.error("Error fetching vendor details: %s", exc)
        return jsonify({"success": False, "message": "Failed to fetch vendor details"}), 500


@vendors_bp.route("/api/vendors/<int:vendor_id>", methods=["PUT"])
@jwt_required()
def update_vendor(vendor_id):
    try:
        data = request.get_json() or {}
        allowed = {
            "name",
            "email",
            "phone",
            "category",
            "status",
            "risk_level",
            "contract_value",
            "rating",
            "country",
        }
        updates = {key: value for key, value in data.items() if key in allowed}
        if not updates:
            return jsonify({"success": False, "message": "No valid fields provided"}), 400

        assignments = ", ".join(f"{column} = ?" for column in updates)
        values = list(updates.values()) + [vendor_id]
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.execute(f"UPDATE vendors SET {assignments} WHERE id = ?", values)
            conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "Vendor not found"}), 404

        return jsonify({"success": True, "message": "Vendor updated successfully"}), 200
    except Exception as exc:
        logger.error("Error updating vendor: %s", exc)
        return jsonify({"success": False, "message": "Failed to update vendor"}), 500


@vendors_bp.route("/api/vendors", methods=["POST"])
@jwt_required()
def create_vendor():
    try:
        data = request.get_json() or {}
        required = ["name", "category"]
        missing = [field for field in required if not data.get(field)]
        if missing:
            return jsonify({"success": False, "message": f"Missing required fields: {', '.join(missing)}"}), 400

        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO vendors(name,email,phone,category,status,risk_level,contract_value,rating,join_date,country)
                VALUES (?,?,?,?,?,?,?,?,date('now'),?)
                """,
                (
                    data["name"],
                    data.get("email", ""),
                    data.get("phone", ""),
                    data["category"],
                    data.get("status", "Active"),
                    data.get("risk_level", "Low"),
                    data.get("contract_value", 0),
                    data.get("rating", 0),
                    data.get("country", "USA"),
                ),
            )
            conn.commit()
            vendor_id = cursor.lastrowid

        return jsonify({"success": True, "message": "Vendor created successfully", "vendor_id": vendor_id}), 201
    except Exception as exc:
        logger.error("Error creating vendor: %s", exc)
        return jsonify({"success": False, "message": "Failed to create vendor"}), 500


@vendors_bp.route("/api/vendors/<int:vendor_id>/performance", methods=["GET"])
@jwt_required()
def get_vendor_performance(vendor_id):
    try:
        performance_data = db_manager.get_performance_data()
        performance_data = performance_data[performance_data["vendor_id"] == vendor_id]
        return jsonify({"success": True, "data": _records(performance_data)}), 200
    except Exception as exc:
        logger.error("Error fetching vendor performance: %s", exc)
        return jsonify({"success": False, "message": "Failed to fetch vendor performance"}), 500


@vendors_bp.route("/api/vendors/<int:vendor_id>/performance", methods=["POST"])
@jwt_required()
def add_performance_metric(vendor_id):
    try:
        data = request.get_json() or {}
        metric_date = data.get("metric_date")
        if not metric_date:
            return jsonify({"success": False, "message": "metric_date is required"}), 400

        on_time_pct = float(data.get("on_time_pct", data.get("delivery_score", 0)))
        defect_rate_pct = float(data.get("defect_rate_pct", data.get("defect_rate", 0)))
        cost_variance = float(data.get("cost_variance", 0))
        quality_score = float(data.get("quality_score", 0))
        overall_score = round((on_time_pct * 0.4) + (quality_score * 0.4) + ((100 - defect_rate_pct * 10) * 0.2), 2)

        with sqlite3.connect(db_manager.db_path) as conn:
            conn.execute(
                """
                INSERT INTO performance_metrics
                (vendor_id, metric_date, on_time_pct, defect_rate_pct, cost_variance, quality_score, overall_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (vendor_id, metric_date, on_time_pct, defect_rate_pct, cost_variance, quality_score, overall_score),
            )
            conn.commit()

        return jsonify({"success": True, "message": "Performance metric added successfully"}), 201
    except Exception as exc:
        logger.error("Error adding performance metric: %s", exc)
        return jsonify({"success": False, "message": "Failed to add performance metric"}), 500


@vendors_bp.route("/api/vendors/export", methods=["GET"])
@jwt_required()
def export_vendors():
    try:
        output = StringIO()
        writer = csv.writer(output)
        vendors = db_manager.get_vendors_with_performance()

        writer.writerow(
            [
                "Vendor ID",
                "Vendor Name",
                "Category",
                "Status",
                "Risk Level",
                "Contract Value",
                "Average Performance",
                "Average On-Time",
                "Average Quality",
            ]
        )
        for _, vendor in vendors.iterrows():
            writer.writerow(
                [
                    vendor.get("vendor_id"),
                    vendor.get("name"),
                    vendor.get("category"),
                    vendor.get("status"),
                    vendor.get("risk_level"),
                    vendor.get("contract_value"),
                    vendor.get("avg_performance"),
                    vendor.get("avg_on_time"),
                    vendor.get("avg_quality"),
                ]
            )

        return output.getvalue(), 200, {
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=vendors_export.csv",
        }
    except Exception as exc:
        logger.error("Error exporting vendors: %s", exc)
        return jsonify({"success": False, "message": "Failed to export vendors"}), 500
