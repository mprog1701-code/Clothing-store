(function() {
    'use strict';

    const THEME_KEY = 'siteTheme';
    const THEME_LIGHT = 'light';
    const THEME_DARK = 'dark';
    const THEME_SYSTEM = 'system';

    function getAppliedTheme(preferredTheme) {
        if (preferredTheme === THEME_SYSTEM || !preferredTheme) {
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? THEME_DARK : THEME_LIGHT;
        }
        return preferredTheme;
    }

    function applyTheme(theme) {
        const isDark = theme === THEME_DARK;
        document.body.classList.toggle('theme-light', !isDark);
        document.documentElement.setAttribute('data-bs-theme', isDark ? THEME_DARK : THEME_LIGHT);
    }

    function setSiteTheme(theme) {
        localStorage.setItem(THEME_KEY, theme);
        const appliedTheme = getAppliedTheme(theme);
        applyTheme(appliedTheme);
    }

    function applyThemeFromPreference() {
        const preferredTheme = localStorage.getItem(THEME_KEY) || THEME_SYSTEM;
        const appliedTheme = getAppliedTheme(preferredTheme);
        applyTheme(appliedTheme);
    }

    // Expose API to global window object
    window.setSiteTheme = setSiteTheme;
    window.applyThemeFromPreference = applyThemeFromPreference;

    // Apply theme on initial load
    applyThemeFromPreference();

    // Watch for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function() {
        const preferredTheme = localStorage.getItem(THEME_KEY);
        if (preferredTheme === THEME_SYSTEM || !preferredTheme) {
            applyThemeFromPreference();
        }
    });

})();
