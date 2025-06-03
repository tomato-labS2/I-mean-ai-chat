import type React from "react"
import type { Metadata, Viewport } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ToastProvider } from "@/components/common/Toast"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "I:mean - Chat with AI",
  description: "AI와 함께하는 스마트한 대화 경험",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "I:mean",
  },
  formatDetection: {
    telephone: false,
  },
  openGraph: {
    type: "website",
    siteName: "I:mean",
    title: "I:mean - Chat with AI",
    description: "AI와 함께하는 스마트한 대화 경험",
  },
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#5a9b5a",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" href="/icon-192x192.png" />
      </head>
      <body className={`${inter.className} antialiased`}>
        <ToastProvider>
          <div className="webapp-container">{children}</div>
        </ToastProvider>
      </body>
    </html>
  )
}
