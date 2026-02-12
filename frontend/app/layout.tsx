import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import "./globals.css"
import { Footer } from "@/components/footer"

const _inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
    title: "AI Batake",
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
            <body className={`font-sans antialiased ${_inter.className} min-h-screen flex flex-col`}>
                <div className="flex-1 flex flex-col">
                    {children}
                </div>
                <Footer />
                {process.env.NODE_ENV === 'production' && <Analytics />}
            </body>
        </html>
    )
}
