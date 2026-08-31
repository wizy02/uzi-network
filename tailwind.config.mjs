/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f0f7ff',
          100: '#dceaff',
          200: '#b8d5ff',
          300: '#8ab8ff',
          400: '#5694ff',
          500: '#2f6ff5',
          600: '#1d4fd9',
          700: '#183ca8',
          800: '#152f7e',
          900: '#0f2160',
        },
        ink: {
          50:  '#f7f8fa',
          100: '#eef0f4',
          200: '#dde1e8',
          300: '#bcc3cf',
          400: '#8e98a8',
          500: '#5d6577',
          600: '#3f4654',
          700: '#2a2f3a',
          800: '#1a1d25',
          900: '#0d0f14',
        },
        accent: '#ff5b3a', // Uzi orange-red
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.7rem', { lineHeight: '1rem' }],
      },
      maxWidth: {
        '8xl': '88rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
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
};