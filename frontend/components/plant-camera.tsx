"use client"

import { useEffect, useState } from "react"
import { Camera } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function PlantCamera() {
    const [imageUrl, setImageUrl] = useState("/healthy-green-tomato-plant-in-smart-greenhouse-wit.jpg")
    const [lastUpdated, setLastUpdated] = useState("2025/01/15 14:32")

    useEffect(() => {
        const fetchImage = async () => {
            try {
                const response = await fetch('/api/plant-camera/latest')
                if (!response.ok) return
                const data = await response.json()
                if (data.image) {
                    setImageUrl(data.image)
                    const date = new Date(data.timestamp)
                    setLastUpdated(date.toLocaleString())
                }
            } catch (error) {
                console.error("Failed to fetch plant image:", error)
            }
        }

        fetchImage()
        const interval = setInterval(fetchImage, 30 * 60 * 1000) // Update every 30 minutes
        return () => clearInterval(interval)
    }, [])

    return (
        <Card className="overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg font-medium flex items-center gap-2">
                    <Camera className="h-5 w-5 text-primary" />
                    プラントカメラ
                </CardTitle>
                <Badge variant="secondary" className="bg-primary/10 text-primary">
                    ライブ
                </Badge>
            </CardHeader>
            <CardContent className="p-0">
                <div className="relative aspect-video">
                    <img src={imageUrl} alt="植物のライブカメラ映像" className="w-full h-full object-cover" />
                    <div className="absolute bottom-3 left-3 bg-card/90 backdrop-blur-sm rounded-md px-3 py-1.5 text-sm">
                        最終更新: {lastUpdated}
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
