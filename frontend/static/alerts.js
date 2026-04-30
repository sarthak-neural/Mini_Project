// Alert Settings Management

function notifyAlert(message, type = 'info') {
    if (typeof showToast === 'function') {
        showToast(message, type, 3500);
        return;
    }
    alert(message);
}

function setAlertButtonLoading(button, isLoading, label = 'Saving...') {
    if (!button) return;
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${label}`;
        button.style.opacity = '0.7';
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || button.innerHTML;
        button.style.opacity = '1';
    }
}

function showAlertSettingsModal() {
    document.getElementById('alertSettingsModal').style.display = 'flex';
    loadAlertPreferences();
}

function closeAlertSettingsModal() {
    document.getElementById('alertSettingsModal').style.display = 'none';
    document.getElementById('alertSettingsForm').reset();
}

// Load alert preferences from server
async function loadAlertPreferences() {
    try {
        const response = await fetch('/api/alerts/preferences');
        const data = await response.json();

        if (data.success) {
            const prefs = data.preferences || {};
            const flat = data.preferences_flat || {};
            const emailEnabled = prefs.email?.enabled ?? prefs.email_enabled ?? false;
            const smsEnabled = prefs.sms?.enabled ?? prefs.sms_enabled ?? false;
            const emailAddress = prefs.email?.email_address ?? prefs.email_address ?? flat.email_address ?? '';
            const phoneNumber = prefs.sms?.phone_number ?? prefs.phone_number ?? flat.phone_number ?? '';
            const threshold =
                prefs.threshold_percentage ??
                prefs.alert_threshold_percentage ??
                flat.threshold_percentage ??
                flat.alert_threshold_percentage ??
                20;

            document.getElementById('email-enabled').checked = emailEnabled;
            document.getElementById('sms-enabled').checked = smsEnabled;
            document.getElementById('alert-email').value = emailAddress;
            document.getElementById('alert-phone').value = phoneNumber;
            document.getElementById('alert-threshold').value = threshold;
            
            // Check if services are available
            if (!data.alerts_available.email) {
                document.getElementById('email-enabled').disabled = true;
            }
            if (!data.alerts_available.sms) {
                document.getElementById('sms-enabled').disabled = true;
            }
        }
    } catch (error) {
        console.error('Error loading alert preferences:', error);
        notifyAlert('Error loading alert preferences: ' + error.message, 'error');
    }
}

// Save alert preferences
document.getElementById('alertSettingsForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const preferences = {
        email_address: document.getElementById('alert-email').value,
        email_enabled: document.getElementById('email-enabled').checked,
        sms_enabled: document.getElementById('sms-enabled').checked,
        phone_number: document.getElementById('alert-phone').value,
        threshold_percentage: parseInt(document.getElementById('alert-threshold').value)
    };

    const submitBtn = this.querySelector('button[type="submit"]');
    setAlertButtonLoading(submitBtn, true, 'Saving...');

    try {
        const response = await fetch('/api/alerts/preferences', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(preferences)
        });

        const data = await response.json();

        if (data.success) {
            notifyAlert('Alert preferences saved successfully!', 'success');
            closeAlertSettingsModal();
        } else {
            notifyAlert('Error saving preferences: ' + data.error, 'error');
        }
    } catch (error) {
        notifyAlert('Error: ' + error.message, 'error');
    } finally {
        setAlertButtonLoading(submitBtn, false);
    }
});

// Send test email alert
async function testEmailAlert() {
    const email = document.getElementById('alert-email').value;
    if (!email) {
        notifyAlert('Please enter an email address first', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/alerts/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ channel: 'email' })
        });

        const data = await response.json();

        if (data.success) {
            notifyAlert('Test email sent successfully! Check your inbox.', 'success');
        } else {
            notifyAlert('Failed to send test email: ' + data.error, 'error');
        }
    } catch (error) {
        notifyAlert('Error: ' + error.message, 'error');
    }
}

// Send test SMS alert
async function testSmsAlert() {
    const phone = document.getElementById('alert-phone').value;
    if (!phone) {
        notifyAlert('Please enter a phone number first', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/alerts/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ channel: 'sms' })
        });

        const data = await response.json();

        if (data.success) {
            notifyAlert('Test SMS sent successfully! Check your phone.', 'success');
        } else {
            notifyAlert('Failed to send test SMS: ' + data.error, 'error');
        }
    } catch (error) {
        notifyAlert('Error: ' + error.message, 'error');
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('alertSettingsModal');
    if (event.target === modal) {
        closeAlertSettingsModal();
    }
}
