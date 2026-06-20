/** @type {import('tailwindcss').Config} */
/*
 * Tailwind configuration for the Portale Khabar front-end.
 *
 * Tailwind is used as a *build tool only* — the compiled CSS is served by
 * Django itself (no separate front-end server). Run:
 *
 *     npm install
 *     npm run watch:css     # while developing
 *     npm run build:css     # for a production-style minified bundle
 *
 * The project ships with a precompiled `static/css/tailwind.css` so you can
 * run it without Node if you don't change the styles.
 */
module.exports = {
  // Dark mode is driven by a `class="dark"` on <html> (we always render dark).
  darkMode: 'class',
  content: [
    // Scan every Django template so utility classes used there survive purge.
    './templates/**/*.html',
    // A little JS can also reference class names.
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      // Brand palette used across the UI (backgrounds, accents, text).
      colors: {
        ink: {
          900: '#0b0f1a',   // page background
          800: '#111726',   // primary surface
          700: '#1a2236',   // elevated surface
          600: '#243049',   // hover/active surface
        },
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',   // primary brand colour (indigo)
          600: '#4f46e5',
          700: '#4338ca',
        },
      },
      // Vazirmatn is the body font; Lalezar is used for big display headings.
      fontFamily: {
        sans: ['Vazirmatn', 'Tahoma', 'system-ui', 'sans-serif'],
        display: ['Lalezar', 'Vazirmatn', 'Tahoma', 'sans-serif'],
      },
      // Glass-card radii / shadows reused across components.
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      boxShadow: {
        glass: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        glow: '0 0 20px rgba(99, 102, 241, 0.35)',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.3s ease-out',
      },
    },
  },
  plugins: [
    // Custom utilities for the glassmorphism look, defined as a small inline
    // plugin so they're available everywhere as Tailwind classes.
    function ({ addComponents }) {
      addComponents({
        // The base "glass panel": translucent + blurred + subtle border.
        '.glass': {
          'background-color': 'rgba(26, 34, 54, 0.55)',
          'backdrop-filter': 'blur(12px)',
          '-webkit-backdrop-filter': 'blur(12px)',
          'border': '1px solid rgba(255, 255, 255, 0.08)',
        },
        '.glass-hover': {
          'transition': 'transform .2s ease, box-shadow .2s ease, background-color .2s ease',
        },
        '.glass-hover:hover': {
          'transform': 'translateY(-4px)',
          'box-shadow': '0 12px 40px 0 rgba(0, 0, 0, 0.45)',
          'background-color': 'rgba(36, 48, 73, 0.65)',
        },
      });
    },
  ],
};
