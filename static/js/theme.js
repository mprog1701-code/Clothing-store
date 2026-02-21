(function() {
    'use strict';
    const THEME_KEY = 'siteTheme';
    const LIGHT_THEME = 'light';

    function applyLightTheme() {
        if (document.body) {
            document.body.classList.add('theme-light');
        }
        document.documentElement.setAttribute('data-bs-theme', 'light');
        document.documentElement.setAttribute('data-theme', 'light');
    }

    window.setSiteTheme = function() {
        try {
            localStorage.setItem(THEME_KEY, LIGHT_THEME);
        } catch (e) {}
        applyLightTheme();
    };

    window.setSiteTheme(LIGHT_THEME);
})();
