// Authentication page JavaScript

// Remember me functionality
const REMEMBER_ME_KEY = 'rememberMeEmail';

function initRememberMe() {
    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const rememberMeCheckbox = document.getElementById('rememberMe');
    
    if (!loginForm) return;
    
    // On page load, check if there's a saved email
    const savedEmail = localStorage.getItem(REMEMBER_ME_KEY);
    if (savedEmail && emailInput) {
        emailInput.value = savedEmail;
        if (rememberMeCheckbox) {
            rememberMeCheckbox.checked = true;
        }
    }
    
    // On form submit, save email if remember me is checked
    loginForm.addEventListener('submit', function(e) {
        if (rememberMeCheckbox && rememberMeCheckbox.checked && emailInput) {
            localStorage.setItem(REMEMBER_ME_KEY, emailInput.value);
        } else {
            localStorage.removeItem(REMEMBER_ME_KEY);
        }
    });
}

// Toggle password visibility
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.getElementById('toggleIcon');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.classList.remove('fa-eye');
        toggleIcon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        toggleIcon.classList.remove('fa-eye-slash');
        toggleIcon.classList.add('fa-eye');
    }
}

// Form validation for signup
const signupForm = document.getElementById('signupForm');
if (signupForm) {
    signupForm.addEventListener('submit', function(e) {
        const password = document.getElementById('password').value;
        const terms = document.querySelector('input[name="terms"]').checked;
        
        if (password.length < 8) {
            e.preventDefault();
            alert('Password must be at least 8 characters long');
            return false;
        }
        
        if (!terms) {
            e.preventDefault();
            alert('Please accept the Terms of Service and Privacy Policy');
            return false;
        }
    });
}

// Form validation for login
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', function(e) {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        if (!email || !password) {
            e.preventDefault();
            alert('Please fill in all fields');
            return false;
        }
    });
}

// Add loading state to buttons
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            submitBtn.disabled = true;
        }
    });
});

// Social auth button handlers
document.querySelectorAll('.btn-social').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        const provider = this.classList.contains('google') ? 'google' : 
                        this.classList.contains('microsoft') ? 'microsoft' : 'apple';
        
        // Show loading state
        const originalHTML = this.innerHTML;
        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        this.disabled = true;
        
        // Redirect to OAuth provider
        window.location.href = `/auth/${provider}`;
    });
});

// Initialize remember me on DOM ready
document.addEventListener('DOMContentLoaded', initRememberMe);
