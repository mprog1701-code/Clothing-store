(function() {
    'use strict';
    const THEME_KEY = 'siteTheme';
    const LIGHT_THEME = 'light';
    const DARK_THEME = 'dark';

    function applyTheme(theme) {
        const html = document.documentElement;
        const isLight = theme === LIGHT_THEME;
        if (document.body) {
            document.body.classList.remove('theme-light', 'dark-theme');
            document.body.classList.add(isLight ? 'theme-light' : 'dark-theme');
        }
        html.setAttribute('data-bs-theme', isLight ? 'light' : 'dark');
        html.setAttribute('data-theme', isLight ? 'light' : 'dark');
    }

    window.setSiteTheme = function(theme) {
        const next = theme === LIGHT_THEME ? LIGHT_THEME : DARK_THEME;
        try {
            localStorage.setItem(THEME_KEY, next);
            localStorage.setItem('theme', next);
        } catch (e) {}
        applyTheme(next);
    };

    try {
        const stored = localStorage.getItem(THEME_KEY) || localStorage.getItem('theme') || DARK_THEME;
        applyTheme(stored);
    } catch (e) {
        applyTheme(DARK_THEME);
    }
})();
