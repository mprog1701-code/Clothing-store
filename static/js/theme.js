(function() {
    'use strict';
    const THEME_KEY = 'siteTheme';
    const THEME_DEFAULT = 'system';

    /**
     * Gets the theme preference from localStorage.
     * @returns {'light'|'dark'|'system'}
     */
    function getThemePref() {
        return localStorage.getItem(THEME_KEY) || THEME_DEFAULT;
    }

    /**
     * Computes if the theme should be dark based on preference.
     * @param {'light'|'dark'|'system'} pref - The user's preference.
     * @returns {boolean} - True if the theme should be dark.
     */
    function computeIsDark(pref) {
        if (pref === 'system') {
            return window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
        return pref === 'dark';
    }

    /**
     * Applies the theme to the document by setting the body class and data-bs-theme attribute.
     */
    function applyTheme() {
        const pref = getThemePref();
        const isDark = computeIsDark(pref);

        document.body.classList.toggle('theme-light', !isDark);
        document.documentElement.setAttribute('data-bs-theme', isDark ? 'dark' : 'light');
    }

    // Make setSiteTheme globally available
    window.setSiteTheme = function(theme) {
        if (['light', 'dark', 'system'].includes(theme)) {
            localStorage.setItem(THEME_KEY, theme);
            applyTheme();
        }
    };

    // Listen for changes in OS theme preference
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        // Only re-apply if the user has selected 'system'
        if (getThemePref() === 'system') {
            applyTheme();
        }
    });

    // Apply the theme on initial load to prevent FOUC
    applyTheme();
})();
