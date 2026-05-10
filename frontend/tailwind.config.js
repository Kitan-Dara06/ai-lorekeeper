/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        lore: {
          dark: '#0a0a1a',
          darker: '#060612',
          card: '#1a1a2e',
          border: '#2a2a3e',
          gold: '#f59e0b',
          'gold-dark': '#d97706',
          purple: '#8b5cf6',
          'purple-dark': '#7c3aed',
          teal: '#14b8a6',
          pink: '#ec4899',
          text: '#e2e8f0',
          'text-muted': '#94a3b8',
        },
      },
      fontFamily: {
        display: ['Georgia', 'serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
