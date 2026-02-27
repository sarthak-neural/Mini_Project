# Automated Alert System Setup Guide

This application now includes an industry-level automated alert system for low stock situations with email and SMS notifications.

## Features

- **Email Alerts**: Send email notifications for low stock situations
- **SMS Alerts**: Send SMS notifications via Twilio
- **Configurable Thresholds**: Set custom low stock alert thresholds
- **Test Alerts**: Verify configuration with test notifications
- **User Preferences**: Each user can manage their own alert settings

## Setup Instructions

### 1. Email Alerts (Gmail Example)

#### Step 1: Enable Gmail App Passwords
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Factor Authentication if not already enabled
3. Go to "App passwords" section
4. Generate new app password for "Mail" on "Windows Computer" (or your device)
5. Copy the 16-character password

#### Step 2: Configure Environment Variables
Create a `.env` file in the project root:

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=noreply@restaurantai.com
```

### 2. SMS Alerts (Twilio)

#### Step 1: Create Twilio Account
1. Go to [Twilio Console](https://www.twilio.com/console)
2. Sign up for a free account (includes $15 trial credits)
3. Get your "Account SID" and "Auth Token"
4. In Phone Numbers, get or purchase a phone number for sending SMS

#### Step 2: Configure Environment Variables
Add to your `.env` file:

```
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Restart the Application

```bash
python app.py
```

## Using Alert Settings

1. Log in to the dashboard
2. Click "Alert Settings" in the Quick Actions section
3. Enter your email address and/or phone number
4. Enable Email/SMS alerts as needed
5. Set the low stock alert threshold percentage
6. Click "Send Test Email" or "Send Test SMS" to verify configuration
7. Save your settings

## Alert Thresholds

The alert threshold percentage determines when alerts are triggered:
- If set to 20%, alert triggers when stock < 20% of the reorder point
- If set to 50%, alert triggers when stock < 50% of the reorder point

## Production Deployment

For production use:

1. **Replace In-Memory Storage**: Current system uses in-memory user storage. Use a proper database (PostgreSQL/MySQL)
2. **Secure Credentials**: Use environment variables or AWS Secrets Manager for sensitive data
3. **Email Service**: Consider using SendGrid, AWS SES, or similar services for better reliability
4. **SMS Service**: Ensure Twilio account has sufficient credits for expected volume
5. **Background Tasks**: Use Celery with Redis/RabbitMQ for async alert sending
6. **Logging**: Implement proper logging and monitoring

## Testing Without Real Services

The system gracefully handles missing services:
- If email is not configured, email alerts will be skipped
- If SMS is not configured, SMS alerts will be skipped
- The UI will show which services are available

## Troubleshooting

### Email alerts not sending
- Check Gmail app password is correct
- Verify 2FA is enabled on Gmail account
- Check firewall allows SMTP (port 587)
- Review application logs

### SMS alerts not sending
- Verify Twilio Account SID and Auth Token
- Check phone number includes country code (+1 for US)
- Ensure Twilio account has credits
- Verify phone numbers are valid

### Test alerts failing
- Check that email/SMS service is configured
- Verify network connectivity
- Check application logs for error details

## API Documentation

### Get Alert Preferences
```
GET /api/alerts/preferences
Authorization: Required (logged in user)
Response: { success, preferences, alerts_available }
```

### Update Alert Preferences
```
POST /api/alerts/preferences
Authorization: Required
Body: { email_enabled, sms_enabled, phone_number, alert_threshold_percentage }
Response: { success, message, preferences }
```

### Send Test Alert
```
POST /api/alerts/test
Authorization: Required
Body: { channel: 'email' or 'sms' }
Response: { success, message }
```

### Check Stock and Send Alerts
```
POST /api/alerts/check-stock
Authorization: Required
Body: { ingredient, current_stock, reorder_point }
Response: { success, alert_triggered, alerts_sent }
```
