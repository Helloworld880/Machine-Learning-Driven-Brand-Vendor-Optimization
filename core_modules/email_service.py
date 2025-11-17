import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime

class EmailService:
    def __init__(self):
        self.config = None
        self.logger = logging.getLogger(__name__)
    
    def set_config(self, config):
        """Set configuration from Config class"""
        self.config = config
    
    def send_email(self, to_email, subject, body, html_body=None):
        """Send email notification via SMTP"""
        try:
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "your_email@gmail.com"
            sender_password = "your_app_password"  # Use Gmail App Password!

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

            print(f"✅ EMAIL SENT TO {to_email}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to send email: {e}")
            print(f"❌ Failed to send email: {e}")
            return False
    
    def send_performance_alert(self, vendor_name, performance_score, threshold=70):
        """Send performance alert email"""
        subject = f"Performance Alert: {vendor_name}"
        body = f"""
Vendor Performance Alert

Vendor: {vendor_name}
Current Performance Score: {performance_score:.1f}%
Threshold: {threshold}%

The vendor's performance has dropped below the acceptable threshold.
Please review and take appropriate action.
"""
        admin_email = "admin@company.com"
        return self.send_email(admin_email, subject, body)
    
    def send_risk_alert(self, vendor_name, risk_level, risk_score):
        """Send risk alert email"""
        subject = f"Risk Alert: {vendor_name} - {risk_level} Risk"
        body = f"""
Vendor Risk Alert

Vendor: {vendor_name}
Risk Level: {risk_level}
Risk Score: {risk_score:.1f}%

This vendor has been identified as high risk.
Immediate attention recommended.
"""
        admin_email = "admin@company.com"
        return self.send_email(admin_email, subject, body)
