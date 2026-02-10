"use client"

import { Leaf } from "lucide-react"
import { useEffect, useState } from "react"

export function LoadingOverlay({ isVisible }: { isVisible: boolean }) {
    const [shouldRender, setShouldRender] = useState(isVisible)

    useEffect(() => {
        if (isVisible) {
            setShouldRender(true)
        } else {
            const timer = setTimeout(() => setShouldRender(false), 500)
            return () => clearTimeout(timer)
        }
    }, [isVisible])

    if (!shouldRender) return null

    return (
        <div
            className={`fixed inset-0 z-[100] flex flex-col items-center justify-center bg-background/80 backdrop-blur-xl transition-opacity duration-500 ${isVisible ? "opacity-100" : "opacity-0 pointer-events-none"
                }`}
        >
            <div className="relative">
                {/* Outer Glow */}
                <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full scale-150 animate-pulse" />

                {/* Main Spinner */}
                <div className="relative flex items-center justify-center">
                    <div className="w-24 h-24 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
                    <div className="absolute">
                        <Leaf className="h-10 w-10 text-primary animate-bounce" />
                    </div>
                </div>
            </div>

            <div className="mt-8 text-center space-y-2">
                <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-green-400">
                    AI Batake
                </h2>
                <p className="text-muted-foreground animate-pulse">
                    データを取得中...
                </p>
            </div>

            {/* Progress Micro-elements */}
            <div className="mt-12 flex gap-2">
                {[0, 1, 2].map((i) => (
                    <div
                        key={i}
                        className="w-2 h-2 rounded-full bg-primary/40 animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                    />
                ))}
            </div>
        </div>
    )
}
