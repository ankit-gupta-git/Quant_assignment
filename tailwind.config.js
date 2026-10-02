/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: '#080b11',
          surface: '#0d121c',
          panel: '#111723',
          panelAlt: '#151d2c',
          border: '#1e293b',
          borderLight: '#2a374d',
          accent: '#0284c7',
          accentGlow: 'rgba(2, 132, 199, 0.15)',
          green: '#10b981',
          greenMuted: '#064e3b',
          red: '#ef4444',
          redMuted: '#450a0a',
          amber: '#f59e0b',
          text: '#f1f5f9',
          muted: '#94a3b8',
          subtle: '#64748b',
          highlight: '#38bdf8'
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', '"Liberation Mono"', '"Courier New"', 'monospace'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
      },
      fontSize: {
        '2xs': '0.65rem',
      }
    },
  },
  plugins: [],
}
