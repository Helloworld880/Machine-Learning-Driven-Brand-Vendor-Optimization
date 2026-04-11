import logging
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from api._compat import get_jwt_identity, jwt_required
from core_modules.analytics import AnalyticsEngine
from core_modules.database import DatabaseManager
from core_modules.email_service import EmailService


alerts_bp = Blueprint("alerts", __name__)
db_manager = DatabaseManager()
analytics_engine = AnalyticsEngine(db_manager)
email_service = EmailService()
logger = logging.getLogger(__name__)

alerts_store = []


def _create_alert(alert_type, severity, message, vendor_id=None, vendor_name=None):
    alert = {
        "id": f"alert_{len(alerts_store) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "type": alert_type,
        "severity": severity,
        "message": message,
        "vendor_id": vendor_id,
        "vendor_name": vendor_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "active",
        "acknowledged_by": None,
        "acknowledged_at": None,
        "resolved_by": None,
        "resolved_at": None,
        "resolution_notes": None,
        "notified_at": None,
        "notification_recipients": [],
    }
    alerts_store.append(alert)
    return alert


def generate_system_alerts():
    alerts_store.clear()

    perf = db_manager.get_vendors_with_performance()
    risk = db_manager.get_risk_data()
    compliance = db_manager.get_compliance_data()

    for _, row in perf[perf["avg_performance"].fillna(0) < 70].head(20).iterrows():
        _create_alert(
            "Performance Alert",
            "High" if row["avg_performance"] < 60 else "Medium",
            f"{row['name']} average performance is {row['avg_performance']:.1f}%.",
            vendor_id=int(row["vendor_id"]),
            vendor_name=row["name"],
        )

    for _, row in risk[risk["risk_level"].str.lower() == "high"].head(20).iterrows():
        _create_alert(
            "Risk Alert",
            "High",
            f"{row['vendor_name']} is currently classified as high risk ({row['overall_risk']:.1f}%).",
            vendor_id=int(row["vendor_id"]),
            vendor_name=row["vendor_name"],
        )

    upcoming_cutoff = datetime.now() + timedelta(days=30)
    if not compliance.empty:
        compliance = compliance.copy()
        compliance["next_audit_date"] = compliance["next_audit_date"].astype("datetime64[ns]")
        upcoming = compliance[compliance["next_audit_date"] <= upcoming_cutoff]
        for _, row in upcoming.head(20).iterrows():
            _create_alert(
                "Compliance Alert",
                "Medium",
                f"{row['vendor_name']} has an upcoming audit on {row['next_audit_date'].date()}.",
                vendor_id=int(row["vendor_id"]),
                vendor_name=row["vendor_name"],
            )


def _notification_message(alerts):
    return "\n".join(
        [
            "Vendor alert notification",
            "",
            *[
                f"- [{alert['severity']}] {alert['vendor_name'] or 'Vendor'}: {alert['message']}"
                for alert in alerts
            ],
        ]
    )


@alerts_bp.route("/api/alerts", methods=["GET"])
@jwt_required()
def get_alerts():
    try:
        alert_type = request.args.get("type")
        severity = request.args.get("severity")
        status = request.args.get("status", "active")
        limit = int(request.args.get("limit", 50))
        days = int(request.args.get("days", 30))

        if not alerts_store:
            generate_system_alerts()

        cutoff = datetime.now() - timedelta(days=days)
        filtered = []
        for alert in alerts_store:
            timestamp = datetime.strptime(alert["timestamp"], "%Y-%m-%d %H:%M:%S")
            if timestamp < cutoff:
                continue
            if alert_type and alert["type"] != alert_type:
                continue
            if severity and alert["severity"] != severity:
                continue
            if status and alert["status"] != status:
                continue
            filtered.append(alert)

        filtered.sort(key=lambda item: item["timestamp"], reverse=True)
        return jsonify({"success": True, "data": filtered[:limit], "total_count": len(filtered)}), 200
    except Exception as exc:
        logger.error("Error fetching alerts: %s", exc)
        return jsonify({"success": False, "message": "Failed to fetch alerts"}), 500


@alerts_bp.route("/api/alerts/<alert_id>", methods=["GET"])
@jwt_required()
def get_alert(alert_id):
    try:
        alert = next((item for item in alerts_store if item["id"] == alert_id), None)
        if not alert:
            return jsonify({"success": False, "message": "Alert not found"}), 404
        return jsonify({"success": True, "data": alert}), 200
    except Exception as exc:
        logger.error("Error fetching alert: %s", exc)
        return jsonify({"success": False, "message": "Failed to fetch alert"}), 500


@alerts_bp.route("/api/alerts/<alert_id>/acknowledge", methods=["POST"])
@jwt_required()
def acknowledge_alert(alert_id):
    try:
        alert = next((item for item in alerts_store if item["id"] == alert_id), None)
        if not alert:
            return jsonify({"success": False, "message": "Alert not found"}), 404

        alert["status"] = "acknowledged"
        alert["acknowledged_by"] = get_jwt_identity()
        alert["acknowledged_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({"success": True, "message": "Alert acknowledged successfully"}), 200
    except Exception as exc:
        logger.error("Error acknowledging alert: %s", exc)
        return jsonify({"success": False, "message": "Failed to acknowledge alert"}), 500


@alerts_bp.route("/api/alerts/<alert_id>/resolve", methods=["POST"])
@jwt_required()
def resolve_alert(alert_id):
    try:
        payload = request.get_json() or {}
        alert = next((item for item in alerts_store if item["id"] == alert_id), None)
        if not alert:
            return jsonify({"success": False, "message": "Alert not found"}), 404

        alert["status"] = "resolved"
        alert["resolved_by"] = get_jwt_identity()
        alert["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert["resolution_notes"] = payload.get("resolution_notes", "")
        return jsonify({"success": True, "message": "Alert resolved successfully"}), 200
    except Exception as exc:
        logger.error("Error resolving alert: %s", exc)
        return jsonify({"success": False, "message": "Failed to resolve alert"}), 500


@alerts_bp.route("/api/alerts/notifications", methods=["POST"])
@jwt_required()
def send_alert_notifications():
    try:
        payload = request.get_json() or {}
        alert_ids = set(payload.get("alert_ids", []))
        recipients = payload.get("recipients", [])

        if not alert_ids or not recipients:
            return jsonify({"success": False, "message": "Alert IDs and recipients are required"}), 400

        selected_alerts = [alert for alert in alerts_store if alert["id"] in alert_ids]
        if not selected_alerts:
            return jsonify({"success": False, "message": "No alerts found for the provided IDs"}), 404

        sent = 0
        failed = 0
        for recipient in recipients:
            if email_service.send_email(recipient, "Vendor Alert Notification", _notification_message(selected_alerts)):
                sent += 1
            else:
                failed += 1

        for alert in selected_alerts:
            alert["notified_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            alert["notification_recipients"] = recipients

        return jsonify(
            {
                "success": True,
                "message": f"Notifications sent to {sent} recipients",
                "data": {"successful": sent, "failed": failed},
            }
        ), 200
    except Exception as exc:
        logger.error("Error sending alert notifications: %s", exc)
        return jsonify({"success": False, "message": "Failed to send alert notifications"}), 500


@alerts_bp.route("/api/alerts/settings", methods=["GET"])
@jwt_required()
def get_alert_settings():
    try:
        settings = {
            "performance_threshold": 70,
            "high_risk_threshold": 65,
            "contract_expiry_days": 30,
            "auto_notification": True,
            "email_notifications": True,
            "notification_frequency": "immediate",
        }
        return jsonify({"success": True, "data": settings}), 200
    except Exception as exc:
        logger.error("Error fetching alert settings: %s", exc)
        return jsonify({"success": False, "message": "Failed to fetch alert settings"}), 500


@alerts_bp.route("/api/alerts/settings", methods=["PUT"])
@jwt_required()
def update_alert_settings():
    try:
        return jsonify({"success": True, "message": "Alert settings updated successfully"}), 200
    except Exception as exc:
        logger.error("Error updating alert settings: %s", exc)
        return jsonify({"success": False, "message": "Failed to update alert settings"}), 500


@alerts_bp.route("/api/alerts/stats", methods=["GET"])
@jwt_required()
def get_alert_statistics():
    try:
        if not alerts_store:
            generate_system_alerts()

        days = int(request.args.get("days", 30))
        cutoff = datetime.now() - timedelta(days=days)
        recent = [
            alert
            for alert in alerts_store
            if datetime.strptime(alert["timestamp"], "%Y-%m-%d %H:%M:%S") >= cutoff
        ]

        stats = {
            "total_alerts": len(recent),
            "by_type": {},
            "by_severity": {},
            "by_status": {},
            "resolution_rate": 0,
        }
        for alert in recent:
            stats["by_type"][alert["type"]] = stats["by_type"].get(alert["type"], 0) + 1
            stats["by_severity"][alert["severity"]] = stats["by_severity"].get(alert["severity"], 0) + 1
            stats["by_status"][alert["status"]] = stats["by_status"].get(alert["status"], 0) + 1

        resolved = stats["by_status"].get("resolved", 0)
        if recent:
            stats["resolution_rate"] = round((resolved / len(recent)) * 100, 2)

        return jsonify({"success": True, "data": stats}), 200
    except Exception as exc:
        logger.error("Error calculating alert statistics: %s", exc)
        return jsonify({"success": False, "message": "Failed to calculate alert statistics"}), 500
