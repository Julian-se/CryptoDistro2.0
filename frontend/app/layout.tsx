import type { Metadata } from 'next'
import './globals.css'
import { Topbar, Sidebar } from '@/components/layout/Sidebar'

export const metadata: Metadata = {
  title: 'CryptoDistro 2.0',
  description: 'P2P Bitcoin on/off-ramp operator dashboard',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-bg-base text-text-primary h-screen flex flex-col overflow-hidden">
        <Topbar />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-y-auto p-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
