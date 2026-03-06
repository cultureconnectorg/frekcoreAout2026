/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        terra: '#C4714A',
        gold: '#D4A84B',
        dark: '#080808',
        navy: '#0D1B2A',
        teal: '#0A4A4A',
        fgreen: '#1A4A2A',
        light: '#F2EDE4',
        mid: '#C8C0B0',
        dim: '#6A6258',
        fwhite: '#FAFAF8',
      },
      fontFamily: {
        display: ['"Bebas Neue"', 'sans-serif'],
        mono: ['"DM Mono"', 'monospace'],
        body: ['"DM Sans"', 'sans-serif'],
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.7s ease forwards',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(30px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
