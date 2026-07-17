/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      colors: {
        bg: '#050505',
        surface: '#121214',
        'surface-raised': '#1a1a1e',
        border: '#242428',
        ink: '#e8e8ea',
        'ink-secondary': '#909096',
        'ink-muted': '#5c5c62',
        accent: '#e8002d',
        'accent-hover': '#cc0028',
        green: {
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        red: {
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
        gray: {
          400: '#a0a0a6',
          500: '#6b6b72',
          600: '#4a4a50',
          700: '#2a2a2e',
          800: '#1e1e22',
          900: '#141416',
          950: '#0a0a0c',
        },
      },
      borderRadius: {
        xl: '0.75rem',
        '2xl': '1rem',
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.4), 0 1px 2px -1px rgb(0 0 0 / 0.3)',
        'card-hover': '0 4px 12px 0 rgb(0 0 0 / 0.5), 0 1px 4px -1px rgb(0 0 0 / 0.3)',
        'dropdown': '0 8px 24px 0 rgb(0 0 0 / 0.6)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.25s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
