import type { Metadata, Viewport } from 'next'
import { fontSans, fontMono } from '../lib/fonts'
import { Header } from '../components/ui/Header'
import { Footer } from '../components/ui/Footer'
import './globals.css'
import '../styles/tokens.css'

export const metadata: Metadata = {
  title: 'Tripline — Blocked isn\'t evidence',
  description:
    'A governed-agent proof layer built for the ArmorIQ Flow State 2026 hackathon. A denial is a verdict, not a record. Tripline turns every denied or held agent action into a signed receipt anyone can verify offline.',
  icons: {
    icon: [
      { url: '/tripline-favicon.svg', type: 'image/svg+xml' },
      { url: '/tripline-favicon-32.png', sizes: '32x32', type: 'image/png' },
    ],
    apple: [
      { url: '/tripline-apple-touch-180.png', sizes: '180x180', type: 'image/png' },
    ],
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  colorScheme: 'dark light',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#F1EEE6' },
    { media: '(prefers-color-scheme: dark)', color: '#0B0B0C' },
  ],
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      className={`${fontSans.variable} ${fontMono.variable} antialiased`}
    >
      <body className="min-h-screen bg-[#0B0B0C] text-[#F3F1EA] font-sans flex flex-col selection:bg-[var(--accent)] selection:text-black">
        <Header />
        <main className="flex-1 w-full" id="main-content">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  )
}
