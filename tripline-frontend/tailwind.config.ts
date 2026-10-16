import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          DEFAULT: '#0B0B0C',
          surface: '#141416',
          surface2: '#1B1B1E',
          border: '#2A2A2E',
          text: '#F3F1EA',
          muted: '#9A9AA2',
          faint: '#6B6B73',
        },
        light: {
          DEFAULT: '#F1EEE6',
          surface: '#FAF8F3',
          border: '#D8D3C6',
          text: '#131313',
          muted: '#5C5951',
          faint: '#8A867B',
        },
        accent: {
          DEFAULT: '#FF4F1A',
          hover: '#E8430F',
          softDark: 'rgba(255, 79, 26, 0.14)',
          softLight: 'rgba(255, 79, 26, 0.10)',
        },
        state: {
          allow: '#2FBF71',
          deny: '#E5484D',
          hold: '#F5A524',
          evaluating: '#4C8DFF',
          verified: '#2FBF71',
          tamper: '#E5484D',
          idle: '#6B6B73',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        badge: '2px',
        card: '4px',
        pill: '9999px',
      },
      maxWidth: {
        contained: '1200px',
      },
    },
  },
  plugins: [],
}

export default config
