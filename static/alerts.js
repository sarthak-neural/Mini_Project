// Alert Settings Management

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
            const prefs = data.preferences;
            document.getElementById('email-enabled').checked = prefs.email_enabled || false;
            document.getElementById('sms-enabled').checked = prefs.sms_enabled || false;
            document.getElementById('alert-phone').value = prefs.phone_number || '';
            document.getElementById('alert-threshold').value = prefs.alert_threshold_percentage || 20;
            
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
    }
}

// Save alert preferences
document.getElementById('alertSettingsForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const preferences = {
        email: document.getElementById('alert-email').value,
        email_enabled: document.getElementById('email-enabled').checked,
        sms_enabled: document.getElementById('sms-enabled').checked,
        phone_number: document.getElementById('alert-phone').value,
        alert_threshold_percentage: parseInt(document.getElementById('alert-threshold').value)
    };

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
            alert('Alert preferences saved successfully!');
            closeAlertSettingsModal();
        } else {
            alert('Error saving preferences: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
});

// Send test email alert
async function testEmailAlert() {
    const email = document.getElementById('alert-email').value;
    if (!email) {
        alert('Please enter an email address first');
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
            alert('✓ Test email sent successfully! Check your inbox.');
        } else {
            alert('✗ Failed to send test email: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Send test SMS alert
async function testSmsAlert() {
    const phone = document.getElementById('alert-phone').value;
    if (!phone) {
        alert('Please enter a phone number first');
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
            alert('✓ Test SMS sent successfully! Check your phone.');
        } else {
            alert('✗ Failed to send test SMS: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('alertSettingsModal');
    if (event.target === modal) {
        closeAlertSettingsModal();
    }
}
