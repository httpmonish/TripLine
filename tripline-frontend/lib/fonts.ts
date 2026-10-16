import localFont from 'next/font/local'

export const fontSans = localFont({
  src: '../public/fonts/geist.woff2',
  variable: '--font-sans',
  display: 'swap',
  fallback: [
    'Inter',
    'system-ui',
    '-apple-system',
    'BlinkMacSystemFont',
    'Segoe UI',
    'Roboto',
    'sans-serif',
  ],
})

export const fontMono = localFont({
  src: '../public/fonts/geist-mono.woff2',
  variable: '--font-mono',
  display: 'swap',
  fallback: [
    'JetBrains Mono',
    'ui-monospace',
    'SFMono-Regular',
    'Menlo',
    'Monaco',
    'Consolas',
    'monospace',
  ],
})
