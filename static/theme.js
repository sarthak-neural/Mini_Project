// Shared Dark Mode Theme System

const THEME_KEY = 'appTheme';

function applyTheme(mode) {
    const isDark = mode === 'dark';
    document.body.classList.toggle('dark-mode', isDark);

    const toggleButton = document.getElementById('theme-toggle');
    if (toggleButton) {
        toggleButton.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        toggleButton.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
    }
}

function initThemeToggle() {
    const storedTheme = localStorage.getItem(THEME_KEY);
    const initialTheme = storedTheme || 'light';
    applyTheme(initialTheme);

    const toggleButton = document.getElementById('theme-toggle');
    if (!toggleButton) return;

    toggleButton.addEventListener('click', () => {
        const nextTheme = document.body.classList.contains('dark-mode') ? 'light' : 'dark';
        localStorage.setItem(THEME_KEY, nextTheme);
        applyTheme(nextTheme);
    });
}

// Initialize on load
document.addEventListener('DOMContentLoaded', initThemeToggle);
