/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Space Grotesk"', 'sans-serif'],
        display: ['"Fraunces"', 'serif'],
      },
      colors: {
        ink: 'var(--color-ink)',
        muted: 'var(--color-muted)',
        surface: 'var(--color-surface)',
        canvas: 'var(--color-canvas)',
        accent: 'var(--color-accent)',
        accent2: 'var(--color-accent-2)',
      },
      boxShadow: {
        soft: '0 20px 50px -30px rgba(15, 23, 42, 0.45)',
        glow: '0 0 0 1px rgba(15, 23, 42, 0.06), 0 10px 40px rgba(14, 116, 144, 0.18)',
      },
      keyframes: {
        floatIn: {
          '0%': { opacity: '0', transform: 'translateY(18px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        floatIn: 'floatIn 0.6s ease-out forwards',
      },
    },
  },
  plugins: [],
};
