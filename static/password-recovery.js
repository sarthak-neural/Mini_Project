// Password recovery functionality

let currentEmail = '';
let currentStep = 1;

document.addEventListener('DOMContentLoaded', function() {
    // Monitor password strength
    const newPasswordInput = document.getElementById('new-password');
    if (newPasswordInput) {
        newPasswordInput.addEventListener('input', function() {
            checkPasswordStrength(this.value);
        });
    }

    // Handle email form submission
    document.getElementById('email-form').addEventListener('submit', function(e) {
        e.preventDefault();
        requestRecoveryCode();
    });

    // Handle code form submission
    document.getElementById('code-form').addEventListener('submit', function(e) {
        e.preventDefault();
        verifyRecoveryCode();
    });

    // Handle password form submission
    document.getElementById('password-form').addEventListener('submit', function(e) {
        e.preventDefault();
        resetPassword();
    });
});

/**
 * Check password strength and update UI
 */
function checkPasswordStrength(password) {
    let strength = 0;
    let strengthText = 'Weak';
    let strengthColor = '#F44336'; // Red

    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[@$!%*?&]/.test(password)) strength++;

    if (strength <= 2) {
        strengthText = 'Weak';
        strengthColor = '#F44336';
    } else if (strength <= 4) {
        strengthText = 'Fair';
        strengthColor = '#FF9800';
    } else if (strength < 6) {
        strengthText = 'Good';
        strengthColor = '#4CAF50';
    } else {
        strengthText = 'Strong';
        strengthColor = '#388E3C';
    }

    const strengthFill = document.getElementById('strength-fill');
    strengthFill.style.backgroundColor = strengthColor;
    strengthFill.style.width = (strength / 6) * 100 + '%';

    const strengthTextEl = document.getElementById('strength-text');
    strengthTextEl.textContent = 'Password strength: ' + strengthText;
    strengthTextEl.style.color = strengthColor;
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const container = document.getElementById('alert-container');
    const alertClass = `alert alert-${type}`;
    const iconClass =
        type === 'success' ? 'fa-check-circle' :
        type === 'error' ? 'fa-times-circle' :
        'fa-info-circle';

    container.innerHTML = `<div class="${alertClass}"><i class="fas ${iconClass}"></i> ${message}</div>`;

    // Auto-hide success and error messages
    if (type !== 'info') {
        setTimeout(() => {
            container.innerHTML = '';
        }, 4000);
    }
}

/**
 * Change active step indicator
 */
function changeStep(step) {
    currentStep = step;

    // Update step indicators
    for (let i = 1; i <= 3; i++) {
        const indicator = document.getElementById(`step${i}-indicator`);
        if (indicator) {
            indicator.classList.remove('active', 'completed');
            if (i < step) {
                indicator.classList.add('completed');
            } else if (i === step) {
                indicator.classList.add('active');
            }
        }
    }

    // Show/hide forms
    document.getElementById('email-form').classList.remove('active');
    document.getElementById('code-form').classList.remove('active');
    document.getElementById('password-form').classList.remove('active');
    document.getElementById('success-form').classList.remove('active');

    if (step === 1) {
        document.getElementById('email-form').classList.add('active');
    } else if (step === 2) {
        document.getElementById('code-form').classList.add('active');
    } else if (step === 3) {
        document.getElementById('password-form').classList.add('active');
    } else if (step === 4) {
        document.getElementById('success-form').classList.add('active');
    }
}

/**
 * Request recovery code
 */
async function requestRecoveryCode() {
    const email = document.getElementById('email').value;

    if (!email) {
        showAlert('Please enter your email address', 'error');
        return;
    }

    try {
        const response = await fetch('/api/auth/request-recovery-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (data.success) {
            currentEmail = email;
            showAlert('Recovery code sent to your email!', 'success');
            changeStep(2);
        } else {
            showAlert(data.error || 'Error sending recovery code', 'error');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
    }
}

/**
 * Verify recovery code
 */
async function verifyRecoveryCode() {
    const code = document.getElementById('verification-code').value;

    if (!code || code.length !== 6) {
        showAlert('Please enter a valid 6-digit code', 'error');
        return;
    }

    try {
        const response = await fetch('/api/auth/verify-recovery-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: currentEmail,
                code: code
            })
        });

        const data = await response.json();

        if (data.success) {
            showAlert('Code verified successfully!', 'success');
            changeStep(3);
        } else {
            showAlert(data.error || 'Invalid verification code', 'error');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
    }
}

/**
 * Reset password
 */
async function resetPassword() {
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    // Validation
    if (newPassword !== confirmPassword) {
        showAlert('Passwords do not match', 'error');
        return;
    }

    if (newPassword.length < 8) {
        showAlert('Password must be at least 8 characters long', 'error');
        return;
    }

    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    if (!passwordRegex.test(newPassword)) {
        showAlert('Password does not meet requirements', 'error');
        return;
    }

    try {
        const response = await fetch('/api/auth/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: currentEmail,
                new_password: newPassword
            })
        });

        const data = await response.json();

        if (data.success) {
            showAlert('Password reset successfully!', 'success');
            changeStep(4);
        } else {
            showAlert(data.error || 'Error resetting password', 'error');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
    }
}

/**
 * Resend recovery code
 */
async function resendCode() {
    if (!currentEmail) {
        showAlert('No email on file. Please go back and enter your email.', 'error');
        return;
    }

    try {
        const response = await fetch('/api/auth/request-recovery-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: currentEmail })
        });

        const data = await response.json();

        if (data.success) {
            showAlert('Recovery code resent to your email!', 'success');
        } else {
            showAlert(data.error || 'Error resending recovery code', 'error');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
    }
}

/**
 * Go back to email form
 */
function goBackToEmail() {
    currentEmail = '';
    document.getElementById('email').value = '';
    document.getElementById('verification-code').value = '';
    changeStep(1);
}
