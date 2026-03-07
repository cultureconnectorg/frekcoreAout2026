/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // FREK Blue - Couleur principale du logo
        frek: {
          50: '#e6f9ff',
          100: '#ccf3ff',
          200: '#99e7ff',
          300: '#66dbff',
          400: '#33cfff',
          500: '#2cc4f5', // Couleur logo exacte
          600: '#23a0c8',
          700: '#1a7c9b',
          800: '#12586e',
          900: '#093441',
        },
        // Couleurs secondaires
        dark: '#050a0d',
        navy: '#0a1520',
        light: '#f0f8ff',
        mid: '#8ab4c8',
        dim: '#4a6b7a',
        // Anciennes couleurs (compatibilité)
        terra: '#2cc4f5',
        gold: '#66dbff',
        fwhite: '#f0f8ff',
      },
      fontFamily: {
        display: ['"Bebas Neue"', 'sans-serif'],
        mono: ['"DM Mono"', 'monospace'],
        body: ['"DM Sans"', 'sans-serif'],
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.7s ease forwards',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(30px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(44, 196, 245, 0.3)' },
          '100%': { boxShadow: '0 0 40px rgba(44, 196, 245, 0.6)' },
        },
      },
    },
  },
  plugins: [],
}
