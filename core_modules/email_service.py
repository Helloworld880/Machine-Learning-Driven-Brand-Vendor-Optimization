import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime
from ai_integration import SmartAlertEngine
from core_modules.config import Config


class EmailService:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.alert_engine = SmartAlertEngine()  # ← AI engine initialized once

    def set_config(self, config):
        """Set configuration from Config class"""
        self.config = config

    def send_email(self, to_email, subject, body, html_body=None):
        """Send email notification via SMTP"""
        try:
            smtp_server = self.config.EMAIL_HOST
            smtp_port = self.config.EMAIL_PORT
            sender_email = self.config.EMAIL_USER
            sender_password = self.config.EMAIL_PASSWORD
            if not sender_email or not sender_password:
                self.logger.warning("Email credentials are not configured. Set EMAIL_USER and EMAIL_PASSWORD.")
                return False

            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = sender_email
            msg["To"] = to_email
            msg["Subject"] = subject

            # Attach plain and HTML versions
            msg.attach(MIMEText(body, "plain"))
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            self.logger.info("Email sent to %s", to_email)
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to send email: {e}")
            return False

    def send_performance_alert(self, vendor_name, performance_score, threshold=70, previous_score=None):
        """
        Send AI-powered performance alert email.
        Now includes smart explanation and recommendation from Claude.
        """
        # ── AI: generate smart explanation ──────────────────────────────────
        try:
            prev = previous_score if previous_score is not None else threshold + 10
            alert = self.alert_engine.explain(
                vendor_name=vendor_name,
                metric="performance score",
                current_value=performance_score,
                previous_value=prev,
                threshold=threshold,
            )
            subject = alert.email_subject
            body = alert.email_body

        except Exception as e:
            # ── Fallback to original static alert if AI fails ────────────────
            self.logger.warning(f"AI alert generation failed, using static alert: {e}")
            subject = f"Performance Alert: {vendor_name}"
            body = f"""
Vendor Performance Alert

Vendor: {vendor_name}
Current Performance Score: {performance_score:.1f}%
Threshold: {threshold}%

The vendor's performance has dropped below the acceptable threshold.
Please review and take appropriate action.
"""
        # ────────────────────────────────────────────────────────────────────

        admin_email = self.config.DEMO_ADMIN_EMAIL
        return self.send_email(admin_email, subject, body)

    def send_risk_alert(self, vendor_name, risk_level, risk_score, previous_risk_score=None):
        """
        Send AI-powered risk alert email.
        Now includes smart explanation and recommendation from Claude.
        """
        # ── AI: generate smart explanation ──────────────────────────────────
        try:
            prev = previous_risk_score if previous_risk_score is not None else risk_score - 15
            alert = self.alert_engine.explain(
                vendor_name=vendor_name,
                metric="risk score",
                current_value=risk_score,
                previous_value=prev,
                threshold=70,
            )
            subject = alert.email_subject
            body = alert.email_body

        except Exception as e:
            # ── Fallback to original static alert if AI fails ────────────────
            self.logger.warning(f"AI alert generation failed, using static alert: {e}")
            subject = f"Risk Alert: {vendor_name} - {risk_level} Risk"
            body = f"""
Vendor Risk Alert

Vendor: {vendor_name}
Risk Level: {risk_level}
Risk Score: {risk_score:.1f}%

This vendor has been identified as high risk.
Immediate attention recommended.
"""
        # ────────────────────────────────────────────────────────────────────

        admin_email = self.config.DEMO_ADMIN_EMAIL
        return self.send_email(admin_email, subject, body)