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
        enterprise: {
          bg: '#F4F5F6',
          surface: '#FFFFFF',
          elevated: '#EAEDF0',
          subtle: '#F0F2F4',
          border: '#CDD2D8',
          text: '#20252B',
          muted: '#59636E',
          faint: '#747F8D',
        },
        diagram: {
          bg: '#181B20',
          surface: '#24272B',
          platform: '#2D3136',
          linework: '#70767D',
          active: '#65BCE7',
          violet: '#9A8AE7',
        },
        dark: {
          DEFAULT: '#181B20',
          surface: '#24272B',
          surface2: '#2D3136',
          border: '#3F444D',
          text: '#F4F5F6',
          muted: '#9EA8B6',
          faint: '#747F8D',
        },
        light: {
          DEFAULT: '#F4F5F6',
          surface: '#FFFFFF',
          border: '#CDD2D8',
          text: '#20252B',
          muted: '#59636E',
          faint: '#747F8D',
        },
        accent: {
          DEFAULT: '#20252B',
          hover: '#2D3136',
          blue: '#65BCE7',
          violet: '#9A8AE7',
          softDark: 'rgba(101, 188, 231, 0.14)',
          softLight: 'rgba(101, 188, 231, 0.08)',
        },
        state: {
          allow: '#10B981',
          deny: '#EF4444',
          hold: '#F59E0B',
          evaluating: '#65BCE7',
          verified: '#10B981',
          tamper: '#EF4444',
          idle: '#747F8D',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        badge: '4px',
        card: '8px',
        pill: '9999px',
      },
      maxWidth: {
        contained: '1280px',
      },
    },
  },
  plugins: [],
}

export default config
