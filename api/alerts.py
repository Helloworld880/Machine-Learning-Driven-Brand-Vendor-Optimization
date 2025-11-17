from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from core.database import DatabaseManager
from core.analytics import AnalyticsEngine
from core.email_service import EmailService
import logging
from datetime import datetime, timedelta

alerts_bp = Blueprint('alerts', __name__)
db_manager = DatabaseManager()
analytics_engine = AnalyticsEngine(db_manager)
email_service = EmailService()

# In-memory storage for alerts (in production, use database)
alerts_store = []

@alerts_bp.route('/api/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    """Get alerts with filtering"""
    try:
        alert_type = request.args.get('type')
        severity = request.args.get('severity')
        status = request.args.get('status', 'active')
        limit = int(request.args.get('limit', 50))
        days = int(request.args.get('days', 30))
        
        # Generate recent alerts if store is empty
        if not alerts_store:
            generate_system_alerts()
        
        # Filter alerts
        filtered_alerts = alerts_store.copy()
        
        if alert_type:
            filtered_alerts = [a for a in filtered_alerts if a['type'] == alert_type]
        
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a['severity'] == severity]
        
        if status:
            filtered_alerts = [a for a in filtered_alerts if a['status'] == status]
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_alerts = [
            a for a in filtered_alerts 
            if datetime.strptime(a['timestamp'], '%Y-%m-%d %H:%M:%S') >= cutoff_date
        ]
        
        # Sort by timestamp (newest first) and apply limit
        filtered_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        filtered_alerts = filtered_alerts[:limit]
        
        return jsonify({
            'success': True,
            'data': filtered_alerts,
            'total_count': len(filtered_alerts)
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching alerts: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch alerts'
        }), 500

@alerts_bp.route('/api/alerts/<alert_id>', methods=['GET'])
@jwt_required()
def get_alert(alert_id):
    """Get specific alert details"""
    try:
        alert = next((a for a in alerts_store if a['id'] == alert_id), None)
        
        if not alert:
            return jsonify({
                'success': False,
                'message': 'Alert not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': alert
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching alert: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch alert'
        }), 500

@alerts_bp.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
@jwt_required()
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        alert = next((a for a in alerts_store if a['id'] == alert_id), None)
        
        if not alert:
            return jsonify({
                'success': False,
                'message': 'Alert not found'
            }), 404
        
        alert['status'] = 'acknowledged'
        alert['acknowledged_by'] = get_jwt_identity()
        alert['acknowledged_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'message': 'Alert acknowledged successfully'
        }), 200
        
    except Exception as e:
        logging.error(f"Error acknowledging alert: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to acknowledge alert'
        }), 500

@alerts_bp.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_alert(alert_id):
    """Resolve an alert"""
    try:
        data = request.get_json()
        resolution_notes = data.get('resolution_notes', '')
        
        alert = next((a for a in alerts_store if a['id'] == alert_id), None)
        
        if not alert:
            return jsonify({
                'success': False,
                'message': 'Alert not found'
            }), 404
        
        alert['status'] = 'resolved'
        alert['resolved_by'] = get_jwt_identity()
        alert['resolved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        alert['resolution_notes'] = resolution_notes
        
        return jsonify({
            'success': True,
            'message': 'Alert resolved successfully'
        }), 200
        
    except Exception as e:
        logging.error(f"Error resolving alert: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to resolve alert'
        }), 500

@alerts_bp.route('/api/alerts/notifications', methods=['POST'])
@jwt_required()
def send_alert_notifications():
    """Send alert notifications via email"""
    try:
        data = request.get_json()
        alert_ids = data.get('alert_ids', [])
        recipients = data.get('recipients', [])
        
        if not alert_ids or not recipients:
            return jsonify({
                'success': False,
                'message': 'Alert IDs and recipients are required'
            }), 400
        
        # Get alerts
        alerts_to_notify = [a for a in alerts_store if a['id'] in alert_ids]
        
        if not alerts_to_notify:
            return jsonify({
                'success': False,
                'message': 'No alerts found for the provided IDs'
            }), 404
        
        # Send notifications
        results = email_service.send_bulk_notifications(
            recipients=recipients,
            subject=f"Vendor Alert Notification - {len(alerts_to_notify)} Alerts",
            message=generate_alert_notification_message(alerts_to_notify),
            notification_type='alerts'
        )
        
        # Update alert notification status
        for alert in alerts_to_notify:
            alert['notified_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            alert['notification_recipients'] = recipients
        
        return jsonify({
            'success': True,
            'message': f"Notifications sent to {results['successful']} recipients",
            'data': results
        }), 200
        
    except Exception as e:
        logging.error(f"Error sending alert notifications: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to send alert notifications'
        }), 500

@alerts_bp.route('/api/alerts/settings', methods=['GET'])
@jwt_required()
def get_alert_settings():
    """Get alert configuration settings"""
    try:
        # In production, this would load from database or config file
        settings = {
            'performance_threshold': 60,
            'risk_threshold': 8.0,
            'contract_expiry_days': 30,
            'auto_notification': True,
            'email_notifications': True,
            'notification_frequency': 'immediate',
            'escalation_rules': {
                'high_risk': ['manager@company.com', 'director@company.com'],
                'contract_expiry': ['procurement@company.com'],
                'performance_alert': ['vendor_manager@company.com']
            }
        }
        
        return jsonify({
            'success': True,
            'data': settings
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching alert settings: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch alert settings'
        }), 500

@alerts_bp.route('/api/alerts/settings', methods=['PUT'])
@jwt_required()
def update_alert_settings():
    """Update alert configuration settings"""
    try:
        data = request.get_json()
        
        # In production, this would save to database or config file
        # For now, we'll just return success
        
        return jsonify({
            'success': True,
            'message': 'Alert settings updated successfully'
        }), 200
        
    except Exception as e:
        logging.error(f"Error updating alert settings: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to update alert settings'
        }), 500

@alerts_bp.route('/api/alerts/stats', methods=['GET'])
@jwt_required()
def get_alert_statistics():
    """Get alert statistics"""
    try:
        days = int(request.args.get('days', 30))
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_alerts = [
            a for a in alerts_store 
            if datetime.strptime(a['timestamp'], '%Y-%m-%d %H:%M:%S') >= cutoff_date
        ]
        
        # Calculate statistics
        stats = {
            'total_alerts': len(recent_alerts),
            'by_type': {},
            'by_severity': {},
            'by_status': {},
            'resolution_rate': 0,
            'average_response_time_hours': 0
        }
        
        for alert in recent_alerts:
            # Count by type
            alert_type = alert['type']
            stats['by_type'][alert_type] = stats['by_type'].get(alert_type, 0) + 1
            
            # Count by severity
            severity = alert['severity']
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            
            # Count by status
            status = alert['status']
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # Calculate resolution rate
        resolved_count = stats['by_status'].get('resolved', 0)
        stats['resolution_rate'] = (resolved_count / len(recent_alerts)) * 100 if recent_alerts else 0
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logging.error(f"Error calculating alert statistics: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to calculate alert statistics'
        }), 500

def generate_system_alerts():
    """Generate system alerts based on current data"""
    global alerts_store
    
    # Clear existing alerts
    alerts_store = []
    
    # Get vendors and generate alerts
    vendors = db_manager.get_vendors()
    
    for vendor in vendors:
        # Performance alerts
        if vendor.get('current_score', 0) < 60:
            create_alert(
                alert_type='Performance Alert',
                severity='High',
                message=f"{vendor['vendor_name']} has low performance score: {vendor.get('current_score', 0):.1f}%",
                vendor_id=vendor['vendor_id'],
                vendor_name=vendor['vendor_name']
            )
        
        # Risk alerts
        if vendor.get('risk_level') == 'High':
            create_alert(
                alert_type='Risk Alert',
                severity='High',
                message=f"{vendor['vendor_name']} is classified as High Risk",
                vendor_id=vendor['vendor_id'],
                vendor_name=vendor['vendor_name']
            )
        
        # Contract expiration alerts
        if vendor.get('contract_end_date'):
            end_date = datetime.strptime(vendor['contract_end_date'], '%Y-%m-%d')
            days_until_expiry = (end_date - datetime.now()).days
            
            if 0 < days_until_expiry <= 30:
                create_alert(
                    alert_type='Contract Alert',
                    severity='Medium',
                    message=f"{vendor['vendor_name']} contract expires in {days_until_expiry} days",
                    vendor_id=vendor['vendor_id'],
                    vendor_name=vendor['vendor_name']
                )
        
        # Financial alerts (simplified)
        if vendor.get('contract_value', 0) > 500000 and vendor.get('current_score', 0) < 70:
            create_alert(
                alert_type='Financial Risk Alert',
                severity='Medium',
                message=f"High-value vendor {vendor['vendor_name']} has performance concerns",
                vendor_id=vendor['vendor_id'],
                vendor_name=vendor['vendor_name']
            )

def create_alert(alert_type, severity, message, vendor_id=None, vendor_name=None):
    """Create a new alert"""
    alert_id = f"alert_{len(alerts_store) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    alert = {
        'id': alert_id,
        'type': alert_type,
        'severity': severity,
        'message': message,
        'vendor_id': vendor_id,
        'vendor_name': vendor_name,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'active',
        'acknowledged_by': None,
        'acknowledged_at': None,
        'resolved_by': None,
        'resolved_at': None,
        'resolution_notes': None,
        'notified_at': None,
        'notification_recipients': []
    }
    
    alerts_store.append(alert)
    return alert_id

def generate_alert_notification_message(alerts):
    """Generate email message for alert notifications"""
    message = f"""
    <h2>Vendor Alert Notification</h2>
    <p>You have {len(alerts)} active vendor alerts requiring attention:</p>
    
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <thead>
            <tr style="background-color: #f8f9fa;">
                <th style="padding: 10px; text-align: left;">Alert Type</th>
                <th style="padding: 10px; text-align: left;">Severity</th>
                <th style="padding: 10px; text-align: left;">Vendor</th>
                <th style="padding: 10px; text-align: left;">Message</th>
                <th style="padding: 10px; text-align: left;">Timestamp</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for alert in alerts:
        message += f"""
            <tr>
                <td style="padding: 8px;">{alert['type']}</td>
                <td style="padding: 8px; color: {'#e74c3c' if alert['severity'] == 'High' else '#f39c12' if alert['severity'] == 'Medium' else '#f1c40f'}">{alert['severity']}</td>
                <td style="padding: 8px;">{alert.get('vendor_name', 'N/A')}</td>
                <td style="padding: 8px;">{alert['message']}</td>
                <td style="padding: 8px;">{alert['timestamp']}</td>
            </tr>
        """
    
    message += """
        </tbody>
    </table>
    
    <p style="margin-top: 20px;">
        <a href="https://vendor-dashboard.company.com/alerts" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            View Alerts in Dashboard
        </a>
    </p>
    
    <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">
        This is an automated notification from the Vendor Performance Management System.
    </p>
    """
    
    return message