// Dark mode functionality
function initDarkMode() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const root = document.documentElement;
    
    // Check system preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');
    
    // Set initial theme
    if (savedTheme) {
        root.setAttribute('data-theme', savedTheme);
    } else if (prefersDark) {
        root.setAttribute('data-theme', 'dark');
    }
    
    // Update toggle button state
    if (darkModeToggle) {
        darkModeToggle.checked = root.getAttribute('data-theme') === 'dark';
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            root.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            if (darkModeToggle) {
                darkModeToggle.checked = e.matches;
            }
        }
    });
}

function toggleDarkMode() {
    const root = document.documentElement;
    const isDark = root.getAttribute('data-theme') === 'dark';
    const newTheme = isDark ? 'light' : 'dark';
    
    root.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Initialize dark mode when the DOM is loaded
document.addEventListener('DOMContentLoaded', initDarkMode);
