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
                <CardContent className="pt-6 pb-6">
                    <div className="flex items-start gap-4">
                        <div className="w-16 h-16 rounded-full bg-muted flex-shrink-0" />
                        <div className="flex-1 space-y-3">
                            <div className="h-4 w-24 bg-muted rounded" />
                            <div className="h-16 bg-muted rounded-lg" />
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
            <CardContent className="pt-6 pb-6">
                <div className="flex items-start gap-4">
                    {/* Character Avatar */}
                    {data?.avatar_url ? (
                        <div className="relative flex-shrink-0">
                            <div className="w-16 h-16 rounded-full overflow-hidden border-4 border-white shadow-lg bg-white">
                                <img
                                    src={data.avatar_url}
                                    alt={data.character_name}
                                    className="w-full h-full object-cover"
                                />
                            </div>
                            <div className="absolute -top-1 -right-1 w-6 h-6 bg-primary rounded-full flex items-center justify-center shadow-md animate-pulse">
                                <Sparkles className="h-3 w-3 text-primary-foreground" />
                            </div>
                        </div>
                    ) : (
                        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center flex-shrink-0 shadow-lg">
                            <Sparkles className="h-8 w-8 text-white" />
                        </div>
                    )}

                    {/* Message Bubble */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                            <span className="text-sm font-bold text-primary">
                                {data?.character_name || "お友達"}
                            </span>
                            <span className="text-xs text-muted-foreground">からのメッセージ</span>
                        </div>
                        <div className="relative">
                            {/* Speech bubble tail */}
                            <div className="absolute -left-2 top-2 w-0 h-0 border-t-8 border-t-transparent border-b-8 border-b-transparent border-r-8 border-r-card" />

                            {/* Message content */}
                            <div className="bg-card rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-border">
                                <p className="text-sm leading-relaxed text-card-foreground whitespace-pre-wrap">
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
