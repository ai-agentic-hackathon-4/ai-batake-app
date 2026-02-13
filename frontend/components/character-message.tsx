"use client"

import { useEffect, useState } from "react"
import { Sparkles, Loader2 } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"

interface CharacterMessageData {
    character_name: string
    message: string
    avatar_url: string | null
}

export function CharacterMessage() {
    const [data, setData] = useState<CharacterMessageData | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const fetchMessage = async () => {
        try {
            setError(null)
            const res = await fetch('/api/character/message')

            if (!res.ok) {
                throw new Error(`Failed to fetch: ${res.status}`)
            }

            const json = await res.json()
            setData(json)
        } catch (err) {
            console.error("Failed to fetch character message:", err)
            setError("メッセージの取得に失敗しました")
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchMessage()

        // Auto-refresh message every 10 minutes
        const interval = setInterval(fetchMessage, 10 * 60 * 1000)

        return () => clearInterval(interval)
    }, [])

    // Don't show component if no character and no message
    if (!isLoading && !data) {
        return null
    }

    // Show loading state
    if (isLoading) {
        return (
            <Card className="animate-pulse">
                <CardContent className="pt-8 pb-8">
                    <div className="flex items-start gap-6">
                        <div className="w-32 h-32 rounded-full bg-muted flex-shrink-0" />
                        <div className="flex-1 space-y-4">
                            <div className="h-6 w-32 bg-muted rounded" />
                            <div className="h-24 bg-muted rounded-lg" />
                        </div>
                    </div>
                </CardContent>
            </Card>
        )
    }

    // Show error state
    if (error) {
        return null // Silently fail, don't show error to user
    }

    // Show message from character
    return (
        <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 via-background to-accent/5 overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-700">
            <CardContent className="pt-8 pb-8">
                <div className="flex flex-col md:flex-row items-center md:items-start gap-4 md:gap-6">
                    {/* Character Avatar */}
                    {data?.avatar_url ? (
                        <div className="relative flex-shrink-0">
                            <div className="w-24 h-24 md:w-32 md:h-32 rounded-full overflow-hidden border-4 border-white shadow-lg bg-white">
                                <img
                                    src={data.avatar_url}
                                    alt={data.character_name}
                                    className="w-full h-full object-cover"
                                />
                            </div>
                            <div className="absolute -top-1 -right-1 w-8 h-8 bg-primary rounded-full flex items-center justify-center shadow-md animate-pulse">
                                <Sparkles className="h-5 w-5 text-primary-foreground" />
                            </div>
                        </div>
                    ) : (
                        <div className="w-24 h-24 md:w-32 md:h-32 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center flex-shrink-0 shadow-lg">
                            <Sparkles className="h-10 w-10 md:h-14 md:w-14 text-white" />
                        </div>
                    )}

                    {/* Message Bubble */}
                    <div className="w-full md:w-auto flex-1 min-w-0">
                        <div className="flex items-center justify-center md:justify-start gap-2 mb-3">
                            <span className="text-lg font-bold text-primary">
                                {data?.character_name || "お友達"}
                            </span>
                            <span className="text-sm text-muted-foreground">からのメッセージ</span>
                        </div>
                        <div className="relative">
                            {/* Speech bubble tail */}
                            <div className="absolute left-1/2 -top-2 -translate-x-1/2 border-l-8 border-l-transparent border-r-8 border-r-transparent border-b-8 border-b-card border-t-0 md:-left-2 md:top-6 md:translate-x-0 md:border-t-8 md:border-t-transparent md:border-b-8 md:border-b-transparent md:border-r-8 md:border-r-card md:border-l-0" />

                            {/* Message content */}
                            <div className="bg-card rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm border border-border text-center md:text-left">
                                <p className="text-base leading-relaxed text-card-foreground whitespace-pre-wrap">
                                    {data?.message || "こんにちは！今日も元気に育てていこうね！🌱"}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
