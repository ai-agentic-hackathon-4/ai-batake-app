"use client"

import { useEffect, useState } from "react"
import { Smile, Frown, Sparkles } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"

interface CharacterMessage {
    message: string
    mood: "happy" | "concerned" | "excited"
    sensor_status: {
        temperature?: number | string
        humidity?: number | string
    }
}

export function CharacterCard() {
    const [characterData, setCharacterData] = useState<CharacterMessage>({
        message: "読み込み中...",
        mood: "happy",
        sensor_status: {}
    })

    useEffect(() => {
        const fetchCharacterMessage = async () => {
            try {
                const res = await fetch('/api/character/message')
                const data = await res.json()
                if (data) {
                    setCharacterData(data)
                }
            } catch (error) {
                console.error("Failed to fetch character message:", error)
                setCharacterData({
                    message: "今日も一緒に見守っていこうね！🌱",
                    mood: "happy",
                    sensor_status: {}
                })
            }
        }

        fetchCharacterMessage()
        // Update every 2 minutes
        const interval = setInterval(fetchCharacterMessage, 120000)
        return () => clearInterval(interval)
    }, [])

    const getMoodIcon = () => {
        switch (characterData.mood) {
            case "excited":
                return <Sparkles className="h-6 w-6 text-primary" />
            case "concerned":
                return <Frown className="h-6 w-6 text-chart-2" />
            default:
                return <Smile className="h-6 w-6 text-primary" />
        }
    }

    const getMoodColor = () => {
        switch (characterData.mood) {
            case "excited":
                return "border-primary/50 bg-primary/5"
            case "concerned":
                return "border-chart-2/50 bg-chart-2/5"
            default:
                return "border-primary/50 bg-primary/5"
        }
    }

    return (
        <Card className={`border-2 ${getMoodColor()} transition-colors duration-500`}>
            <CardContent className="pt-6">
                <div className="flex items-start gap-4">
                    {/* Character Avatar */}
                    <div className="flex-shrink-0">
                        <div className="relative">
                            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center border-2 border-primary/30">
                                <span className="text-3xl">🌱</span>
                            </div>
                            <div className="absolute -bottom-1 -right-1 bg-background rounded-full p-1 border-2 border-background">
                                {getMoodIcon()}
                            </div>
                        </div>
                    </div>

                    {/* Speech Bubble */}
                    <div className="flex-1 min-w-0">
                        <div className="relative">
                            {/* Speech bubble triangle */}
                            <div className="absolute -left-2 top-3 w-0 h-0 border-t-8 border-t-transparent border-b-8 border-b-transparent border-r-8 border-r-card" />
                            
                            {/* Message content */}
                            <div className="bg-card rounded-lg p-4 shadow-sm border border-border">
                                <p className="text-sm font-medium text-card-foreground leading-relaxed">
                                    {characterData.message}
                                </p>
                            </div>
                        </div>
                        
                        {/* Character name */}
                        <p className="text-xs text-muted-foreground mt-2 ml-2">
                            畑の見守りキャラクター
                        </p>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
