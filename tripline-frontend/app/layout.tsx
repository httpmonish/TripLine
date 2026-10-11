import type { Metadata, Viewport } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Tripline — Blocked isn’t evidence',
  description: 'An evidence layer for AI agent actions. Every denied action gets a signed receipt.',
  generator: 'Tripline Phase 9',
  icons: {
    icon: [
      {
        url: '/tripline-favicon.svg',
        type: 'image/svg+xml',
      },
      {
        url: '/tripline-favicon-32.png',
        sizes: '32x32',
        type: 'image/png',
      },
    ],
    apple: [
      {
        url: '/tripline-apple-touch-180.png',
        sizes: '180x180',
        type: 'image/png',
      },
    ],
  },
}

export const viewport: Viewport = {
  colorScheme: 'light dark',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: 'white' },
    { media: '(prefers-color-scheme: dark)', color: 'black' },
  ],
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}

