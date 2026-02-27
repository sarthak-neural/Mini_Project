import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Email configuration
try:
    from flask_mail import Mail, Message
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

# SMS configuration (Twilio)
try:
    from twilio.rest import Client
    SMS_AVAILABLE = True
except ImportError:
    SMS_AVAILABLE = False


class AlertManager:
    """
    Manages automated alerts for low stock situations.
    Supports email and SMS notifications.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.mail = None
        self.twilio_client = None
        
        if EMAIL_AVAILABLE and app:
            self.mail = Mail(app)
        
        if SMS_AVAILABLE:
            try:
                self.twilio_client = Client(
                    os.getenv('TWILIO_ACCOUNT_SID'),
                    os.getenv('TWILIO_AUTH_TOKEN')
                )
            except Exception as e:
                logger.warning(f"Twilio not configured: {e}")
    
    def send_low_stock_alert(self, user_data, ingredient, current_stock, reorder_point, alert_preferences):
        """
        Send low stock alert via preferred channels (email/SMS).
        """
        alerts_sent = []
        
        # Prepare alert message
        subject = f"Low Stock Alert: {ingredient}"
        message = f"""
Low Stock Alert for {ingredient}

Current Stock: {current_stock} units
Reorder Point: {reorder_point} units
Recommended Action: Place an order immediately

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Send email if enabled
        if alert_preferences.get('email_enabled', False) and EMAIL_AVAILABLE and self.mail:
            try:
                email = user_data.get('email')
                if email:
                    msg = Message(
                        subject=subject,
                        recipients=[email],
                        body=message,
                        sender=os.getenv('MAIL_DEFAULT_SENDER', 'noreply@restaurantai.com')
                    )
                    self.mail.send(msg)
                    alerts_sent.append('email')
                    logger.info(f"Email alert sent to {email} for {ingredient}")
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
        
        # Send SMS if enabled
        if alert_preferences.get('sms_enabled', False) and SMS_AVAILABLE and self.twilio_client:
            try:
                phone = alert_preferences.get('phone_number')
                if phone:
                    sms_message = f"Low Stock Alert: {ingredient} is at {current_stock} units (reorder point: {reorder_point}). Place an order immediately."
                    
                    self.twilio_client.messages.create(
                        body=sms_message,
                        from_=os.getenv('TWILIO_PHONE_NUMBER'),
                        to=phone
                    )
                    alerts_sent.append('sms')
                    logger.info(f"SMS alert sent to {phone} for {ingredient}")
            except Exception as e:
                logger.error(f"Failed to send SMS alert: {e}")
        
        return alerts_sent
    
    def send_reorder_reminder(self, user_data, ingredient, suggested_quantity, alert_preferences):
        """
        Send reorder reminder alert.
        """
        alerts_sent = []
        
        subject = f"Reorder Reminder: {ingredient}"
        message = f"""
Reorder Reminder for {ingredient}

Suggested Order Quantity: {suggested_quantity} units
This quantity optimizes for your demand forecast and lead time.

Please place an order at your earliest convenience.
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Send email if enabled
        if alert_preferences.get('email_enabled', False) and EMAIL_AVAILABLE and self.mail:
            try:
                email = user_data.get('email')
                if email:
                    msg = Message(
                        subject=subject,
                        recipients=[email],
                        body=message,
                        sender=os.getenv('MAIL_DEFAULT_SENDER', 'noreply@restaurantai.com')
                    )
                    self.mail.send(msg)
                    alerts_sent.append('email')
            except Exception as e:
                logger.error(f"Failed to send reorder reminder: {e}")
        
        return alerts_sent
    
    def test_alert(self, contact_info, channel='email'):
        """
        Send a test alert to verify configuration.
        """
        try:
            if channel == 'email' and EMAIL_AVAILABLE and self.mail:
                msg = Message(
                    subject="Test Alert - Restaurant Inventory AI",
                    recipients=[contact_info],
                    body="This is a test alert. Your email alerts are configured correctly.",
                    sender=os.getenv('MAIL_DEFAULT_SENDER', 'noreply@restaurantai.com')
                )
                self.mail.send(msg)
                return True
            
            elif channel == 'sms' and SMS_AVAILABLE and self.twilio_client:
                self.twilio_client.messages.create(
                    body="Test alert from Restaurant Inventory AI. Your SMS alerts are configured correctly.",
                    from_=os.getenv('TWILIO_PHONE_NUMBER'),
                    to=contact_info
                )
                return True
        except Exception as e:
            logger.error(f"Failed to send test alert: {e}")
            return False
        
        return False


alert_manager = None


def init_alerts(app):
    """
    Initialize alert manager with Flask app.
    """
    global alert_manager
    alert_manager = AlertManager(app)
    return alert_manager
