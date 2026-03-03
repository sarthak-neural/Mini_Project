// Settings page functionality

document.addEventListener('DOMContentLoaded', function() {
    loadUserProfile();
    loadLocationSettings();
    loadNotificationSettings();
});

// Switch between settings panels
function switchPanel(panelName) {
    // Hide all panels
    document.querySelectorAll('.settings-panel').forEach(panel => {
        panel.classList.remove('active');
    });

    // Remove active from all menu links
    document.querySelectorAll('.settings-menu-link').forEach(link => {
        link.classList.remove('active');
    });

    // Show selected panel
    const panel = document.getElementById(panelName + '-panel');
    if (panel) {
        panel.classList.add('active');
    }

    // Mark menu link as active
    event.target.classList.add('active');
}

// Load user profile information
async function loadUserProfile() {
    try {
        const response = await fetch('/api/user/profile');
        const data = await response.json();

        if (data.success) {
            const user = data.user;
            document.getElementById('first-name').value = user.first_name || '';
            document.getElementById('last-name').value = user.last_name || '';
            document.getElementById('restaurant-name').value = user.restaurant_name || '';
        }
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

// Load location and unit settings
async function loadLocationSettings() {
    try {
        const response = await fetch('/api/user/location');
        const data = await response.json();

        if (data.success) {
            const location = data.location;
            if (location.country) {
                document.getElementById('country').value = location.country;
            }
            if (location.city) {
                document.getElementById('city').value = location.city;
            }

            // Update unit display
            if (data.units) {
                document.getElementById('weight-unit').textContent = data.units.weight || '-';
                document.getElementById('volume-unit').textContent = data.units.volume || '-';
                document.getElementById('currency').textContent = data.units.currency || '-';
            }
        }
    } catch (error) {
        console.error('Error loading location:', error);
    }
}

// Load notification settings
async function loadNotificationSettings() {
    try {
        const response = await fetch('/api/alerts/preferences');
        const data = await response.json();

        if (data.success) {
            const prefs = data.preferences;
            document.getElementById('alert-email').value = prefs.email?.email_address || '';
            document.getElementById('email-alerts').checked = prefs.email?.enabled || false;
            document.getElementById('alert-phone').value = prefs.sms?.phone_number || '';
            document.getElementById('sms-alerts').checked = prefs.sms?.enabled || false;
            document.getElementById('alert-threshold').value = prefs.threshold_percentage || 20;
        }
    } catch (error) {
        console.error('Error loading notification settings:', error);
    }
}

// Update country/units
document.getElementById('country').addEventListener('change', async function() {
    const country = this.value;
    if (!country) return;

    const unitStandards = {
        'US': { weight: 'lbs', volume: 'fl oz', currency: 'USD' },
        'GB': { weight: 'lbs', volume: 'fl oz', currency: 'GBP' },
        'CA': { weight: 'kg', volume: 'ml', currency: 'CAD' },
        'AU': { weight: 'kg', volume: 'ml', currency: 'AUD' },
        'IN': { weight: 'kg', volume: 'ml', currency: 'INR' },
        'DE': { weight: 'kg', volume: 'ml', currency: 'EUR' },
        'FR': { weight: 'kg', volume: 'ml', currency: 'EUR' },
        'JP': { weight: 'kg', volume: 'ml', currency: 'JPY' },
        'CN': { weight: 'kg', volume: 'ml', currency: 'CNY' },
        'MX': { weight: 'kg', volume: 'ml', currency: 'MXN' },
        'BR': { weight: 'kg', volume: 'ml', currency: 'BRL' },
    };

    const units = unitStandards[country] || unitStandards['US'];
    document.getElementById('weight-unit').textContent = units.weight;
    document.getElementById('volume-unit').textContent = units.volume;
    document.getElementById('currency').textContent = units.currency;
});

// Save profile form
document.getElementById('profile-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const data = {
        first_name: document.getElementById('first-name').value,
        last_name: document.getElementById('last-name').value,
        restaurant_name: document.getElementById('restaurant-name').value
    };

    try {
        const response = await fetch('/api/user/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        const alertDiv = document.getElementById('profile-alert');

        if (result.success) {
            alertDiv.innerHTML = '<div class="alert alert-success"><i class="fas fa-check-circle"></i> Profile updated successfully!</div>';
            setTimeout(() => {
                alertDiv.innerHTML = '';
            }, 3000);
        } else {
            alertDiv.innerHTML = '<div class="alert alert-error"><i class="fas fa-times-circle"></i> Error: ' + (result.error || 'Unknown error') + '</div>';
        }
    } catch (error) {
        const alertDiv = document.getElementById('profile-alert');
        alertDiv.innerHTML = '<div class="alert alert-error"><i class="fas fa-times-circle"></i> Error: ' + error.message + '</div>';
    }
});

// Save location form
document.getElementById('location-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const data = {
        country: document.getElementById('country').value,
        city: document.getElementById('city').value
    };

    try {
        const response = await fetch('/api/location/country', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        const alertDiv = document.getElementById('location-alert');

        if (result.success) {
            alertDiv.innerHTML = '<div class="alert alert-success"><i class="fas fa-check-circle"></i> Location updated successfully!</div>';
            setTimeout(() => {
                alertDiv.innerHTML = '';
            }, 3000);
        } else {
            alertDiv.innerHTML = '<div class="alert alert-error"><i class="fas fa-times-circle"></i> Error: ' + (result.error || 'Unknown error') + '</div>';
        }
    } catch (error) {
        const alertDiv = document.getElementById('location-alert');
        alertDiv.innerHTML = '<div class="alert alert-error"><i class="fas fa-times-circle"></i> Error: ' + error.message + '</div>';
    }
});

// Save notification preferences
document.getElementById('notifications-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const data = {
        email_address: document.getElementById('alert-email').value,
        email_enabled: document.getElementById('email-alerts').checked,
        phone_number: document.getElementById('alert-phone').value,
        sms_enabled: document.getElementById('sms-alerts').checked,
        threshold_percentage: parseInt(document.getElementById('alert-threshold').value)
    };

    try {
        const response = await fetch('/api/alerts/preferences', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        const alertDiv = document.getElementById('notifications-alert');

        if (result.success) {
            alertDiv.innerHTML = '<div class="alert alert-success"><i class="fas fa-check-circle"></i> Notification preferences updated!</div>';
            setTimeout(() => {
                alertDiv.innerHTML = '';
            }, 3000);
        } else {
            alertDiv.innerHTML = '<div class="alert alert-error"><i class="fas fa-times-circle"></i> Error: ' + (result.error || 'Unknown error') + '</div>';
        }
    } catch (error) {
        const alertDiv = document.getElementById('notifications-alert');
        alertDiv.innerHTML = '<div class="alert alert-error"><i class="fas fa-times-circle"></i> Error: ' + error.message + '</div>';
    }
});

// Change password form
document.getElementById('password-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('new-password-confirm').value;

    // Validation
    if (newPassword !== confirmPassword) {
        alert('New passwords do not match!');
        return;
    }

    if (newPassword.length < 8) {
        alert('Password must be at least 8 characters long!');
        return;
    }

    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    if (!passwordRegex.test(newPassword)) {
        alert('Password must contain uppercase, lowercase, number, and special character!');
        return;
    }

    try {
        const response = await fetch('/api/user/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        const result = await response.json();
        const alertDiv = document.getElementById('security-alert');

        if (result.success) {
            alertDiv.innerHTML = '<div class="alert alert-success"><i class="fas fa-check-circle"></i> Password changed successfully!</div>';
            document.getElementById('password-form').reset();
            setTimeout(() => {
                alertDiv.innerHTML = '';
            }, 3000);
        } else {
            alertDiv.innerHTML = '<div class="alert alert-error"><i class="fas fa-times-circle"></i> Error: ' + (result.error || 'Unknown error') + '</div>';
        }
    } catch (error) {
        const alertDiv = document.getElementById('security-alert');
        alertDiv.innerHTML = '<div class="alert alert-error"><i class="fas fa-times-circle"></i> Error: ' + error.message + '</div>';
    }
});

// Test alert notification
async function testAlertNotification() {
    const email = document.getElementById('alert-email').value;

    if (!email) {
        alert('Please enter an email address first!');
        return;
    }

    try {
        const response = await fetch('/api/alerts/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: email,
                type: 'test'
            })
        });

        const result = await response.json();
        const alertDiv = document.getElementById('notifications-alert');

        if (result.success) {
            alertDiv.innerHTML = '<div class="alert alert-success"><i class="fas fa-check-circle"></i> Test email sent! Check your inbox.</div>';
            setTimeout(() => {
                alertDiv.innerHTML = '';
            }, 3000);
        } else {
            alertDiv.innerHTML = '<div class="alert alert-error"><i class="fas fa-times-circle"></i> Error: ' + (result.error || 'Unknown error') + '</div>';
        }
    } catch (error) {
        const alertDiv = document.getElementById('notifications-alert');
        alertDiv.innerHTML = '<div class="alert alert-error"><i class="fas fa-times-circle"></i> Error: ' + error.message + '</div>';
    }
}

// Confirm delete account
function confirmDeleteAccount() {
    if (confirm('Are you sure? This action cannot be undone. Type "DELETE" to confirm.')) {
        const confirmation = prompt('Type "DELETE" to confirm account deletion:');
        if (confirmation === 'DELETE') {
            deleteAccount();
        } else {
            alert('Account deletion cancelled.');
        }
    }
}

// Delete account
async function deleteAccount() {
    try {
        const response = await fetch('/api/user/delete-account', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (result.success) {
            alert('Account deleted successfully. You will be logged out.');
            window.location.href = '/logout';
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}
