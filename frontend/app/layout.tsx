import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import "./globals.css"

const _inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
    title: "Saib-AI",
    description: "AI-powered smart farming monitoring dashboard",
    generator: "v0.app",
}

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode
}>) {
    return (
        <html lang="ja">
            <body className={`font-sans antialiased ${_inter.className}`}>
                {children}
                {process.env.NODE_ENV === 'production' && <Analytics />}
            </body>
        </html>
    )
}
