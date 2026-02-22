// Landing page JavaScript

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Animate features on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.feature-card, .benefit-item, .showcase-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'all 0.6s ease';
    observer.observe(el);
});

// Add scroll effect to navbar
window.addEventListener('scroll', () => {
    const nav = document.querySelector('.landing-nav');
    if (nav) {
        nav.classList.toggle('nav-scrolled', window.scrollY > 100);
    }
});

// Animate chart bars
const animateBars = () => {
    const bars = document.querySelectorAll('.bar');
    bars.forEach((bar, index) => {
        setTimeout(() => {
            bar.style.opacity = '0';
            bar.style.transform = 'scaleY(0)';
            setTimeout(() => {
                bar.style.transition = 'all 0.8s ease';
                bar.style.opacity = '1';
                bar.style.transform = 'scaleY(1)';
            }, 100);
        }, index * 100);
    });
};

// Run animation when dashboard preview is visible
const previewObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateBars();
            // Animate only preview counters
            const previewCounters = entry.target.querySelectorAll('.counter');
            animateCounters(previewCounters);
            previewObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

const preview = document.querySelector('.dashboard-preview');
if (preview) {
    previewObserver.observe(preview);
}

// Run animation when showcase cards are visible
const showcaseObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            // Animate showcase counters
            const showcaseCounters = entry.target.querySelectorAll('.counter');
            animateCounters(showcaseCounters);
            showcaseObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.3 });

const showcase = document.querySelector('.stats-showcase');
if (showcase) {
    showcaseObserver.observe(showcase);
}

// Animate counter numbers with vertical rolling effect
function animateCounters(counterElements) {
    if (!counterElements || counterElements.length === 0) {
        counterElements = document.querySelectorAll('.counter');
    }
    
    // Animate all counters in sync
    const duration = 2000;
    const steps = 60;
    const stepDuration = duration / steps;
    let currentStep = 0;
    
    // Add transition style to all counters
    counterElements.forEach(counter => {
        counter.style.transition = 'transform 0.05s ease, opacity 0.05s ease';
        counter.style.display = 'inline-block';

        const currencySymbol = counter.parentElement?.querySelector('.currency-symbol');
        if (currencySymbol) {
            currencySymbol.style.transition = 'transform 0.05s ease, opacity 0.05s ease';
            currencySymbol.style.display = 'inline-block';
        }
    });
    
    const animate = () => {
        if (currentStep <= steps) {
            const progress = currentStep / steps;
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            
            // Animate all counters together
            counterElements.forEach(counter => {
                const target = parseInt(counter.getAttribute('data-target'));
                const currentValue = Math.floor(easeOutQuart * target);
                
                // Format the display value
                if (currentValue >= 1000) {
                    counter.textContent = currentValue.toLocaleString();
                } else {
                    counter.textContent = currentValue;
                }
                
                // Vertical rolling animation
                counter.style.transform = 'translateY(-8px)';
                counter.style.opacity = '0.6';

                const currencySymbol = counter.parentElement?.querySelector('.currency-symbol');
                if (currencySymbol) {
                    currencySymbol.style.transform = 'translateY(-8px)';
                    currencySymbol.style.opacity = '0.6';
                }
                
                // Reset position smoothly
                setTimeout(() => {
                    counter.style.transform = 'translateY(0)';
                    counter.style.opacity = '1';

                    const currencySymbol = counter.parentElement?.querySelector('.currency-symbol');
                    if (currencySymbol) {
                        currencySymbol.style.transform = 'translateY(0)';
                        currencySymbol.style.opacity = '1';
                    }
                }, 25);
            });
            
            currentStep++;
            setTimeout(animate, stepDuration);
        } else {
            // Final values - format properly
            counterElements.forEach(counter => {
                const target = parseInt(counter.getAttribute('data-target'));
                
                if (target >= 1000) {
                    counter.textContent = target.toLocaleString();
                } else {
                    counter.textContent = target;
                }
                counter.style.transform = 'translateY(0)';
                counter.style.opacity = '1';

                const currencySymbol = counter.parentElement?.querySelector('.currency-symbol');
                if (currencySymbol) {
                    currencySymbol.style.transform = 'translateY(0)';
                    currencySymbol.style.opacity = '1';
                }
            });
        }
    };
    
    animate();
}
// Display location and units info on the page
function displayLocationInfo() {
    const locationInfo = document.createElement('div');
    locationInfo.id = 'location-banner';
    locationInfo.className = 'location-banner';
    locationInfo.innerHTML = `
        <div class="location-banner-content">
            <span id="location-text"><i class="fas fa-map-marker-alt"></i> Location: Detecting...</span>
            <span id="units-text" style="margin-left: 1rem;"></span>
            <button class="btn btn-secondary-outline" onclick="showLocationModal()" style="margin-left: auto; padding: 0.5rem 1rem; font-size: 0.9rem;">
                <i class="fas fa-sync-alt"></i> Change Location
            </button>
        </div>
    `;
    
    // Insert after navbar
    const nav = document.querySelector('.landing-nav');
    if (nav && nav.parentElement) {
        nav.parentElement.insertBefore(locationInfo, nav.nextSibling);
    }
    
    // Update with actual location
    const stored = locationService.loadFromStorage();
    console.log('💾 Loaded location data:', stored);
    if (locationService.country) {
        // Add small delay to ensure DOM is ready
        setTimeout(() => {
            console.log('🔄 Calling updateLocationDisplay after DOM ready');
            updateLocationDisplay();
        }, 100);
    } else {
        updateCurrencySymbols();
    }
}

function updateCurrencySymbols() {
    const currency = (locationService.units && locationService.units.currency) ? locationService.units.currency : 'USD';
    const symbol = locationService.getUnitSymbol(currency);
    document.querySelectorAll('.currency-symbol').forEach(el => {
        el.textContent = symbol;
    });
}

function updateLocationDisplay() {
    const locationText = document.getElementById('location-text');
    const unitsText = document.getElementById('units-text');
    
    console.log('🔄 updateLocationDisplay called');
    console.log('📍 Current locationService.country:', locationService.country);
    console.log('📏 Current locationService.units:', locationService.units);
    
    if (locationService.country) {
        const countryNames = {
            'US': 'United States',
            'GB': 'United Kingdom',
            'CA': 'Canada',
            'AU': 'Australia',
            'IN': 'India',
            'DE': 'Germany',
            'FR': 'France',
            'JP': 'Japan',
            'CN': 'China',
            'MX': 'Mexico',
            'BR': 'Brazil'
        };
        
        const country = countryNames[locationService.country] || locationService.country;
        if (locationText) {
            locationText.innerHTML = `<i class="fas fa-map-marker-alt"></i> Location: <strong>${country}</strong>`;
        }
        
        if (unitsText && locationService.units) {
            const weight = locationService.units.weight || 'kg';
            const volume = locationService.units.volume || 'ml';
            const currency = locationService.units.currency || 'USD';
            const currencySymbol = locationService.getUnitSymbol(currency);
            console.log('✅ Displaying units:', { weight, volume, currency, currencySymbol });
            unitsText.innerHTML = `
                <span><strong>Units:</strong> ${weight} | ${volume} | ${currencySymbol} ${currency}</span>
            `;
        } else {
            console.log('⚠️ Units not available:', { unitsText: !!unitsText, units: locationService.units });
        }

        updateCurrencySymbols();
    } else {
        console.log('⚠️ Country not set');
        if (locationText) {
            locationText.innerHTML = `<i class="fas fa-map-marker-alt"></i> Location: <strong>Not Set</strong>`;
        }
        updateCurrencySymbols();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOMContentLoaded - Initializing landing page');
    
    // Display location banner (this will call loadFromStorage and updateLocationDisplay)
    displayLocationInfo();
    
    // Check if location is already set - use the already-loaded data
    if (!locationService.country) {
        console.log('⚠️ No location set, will show modal');
        // Show location modal automatically if location not set
        setTimeout(() => {
            showLocationModal();
        }, 1000); // Show after 1 second for better UX
    } else {
        console.log('✅ Location already set:', locationService.country, locationService.units);
    }
});