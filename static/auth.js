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

// Attach location data to form hidden inputs
function attachLocationToForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    // Check if location is already in hidden inputs (from URL redirect)
    const existingCountry = form.querySelector('input[name="country"]');
    if (existingCountry && existingCountry.value) {
        console.log('✅ Location already in form from URL:', existingCountry.value);
        return;
    }
    
    try {
        // Get location data from localStorage via locationService
        const storedData = localStorage.getItem('userLocation');
        if (storedData) {
            const locationData = JSON.parse(storedData);
            
            if (locationData.country || (locationData.location && locationData.location.country)) {
                const country = locationData.country || locationData.location.country;
                // Add country hidden input
                const countryInput = document.createElement('input');
                countryInput.type = 'hidden';
                countryInput.name = 'country';
                countryInput.value = country;
                form.appendChild(countryInput);
                console.log('✅ Attached country to form from localStorage:', country);
            }
            
            if (locationData.location && locationData.location.city) {
                // Add city hidden input
                const cityInput = document.createElement('input');
                cityInput.type = 'hidden';
                cityInput.name = 'city';
                cityInput.value = locationData.location.city;
                form.appendChild(cityInput);
            }
            
            if (locationData.location && locationData.location.latitude) {
                // Add latitude hidden input
                const latInput = document.createElement('input');
                latInput.type = 'hidden';
                latInput.name = 'latitude';
                latInput.value = locationData.location.latitude;
                form.appendChild(latInput);
            }
            
            if (locationData.location && locationData.location.longitude) {
                // Add longitude hidden input
                const lngInput = document.createElement('input');
                lngInput.type = 'hidden';
                lngInput.name = 'longitude';
                lngInput.value = locationData.location.longitude;
                form.appendChild(lngInput);
            }
        } else {
            console.log('ℹ️ No location data found in localStorage');
        }
    } catch (error) {
        console.error('Error attaching location to form:', error);
    }
}

// Initialize remember me on DOM ready
document.addEventListener('DOMContentLoaded', initRememberMe);
