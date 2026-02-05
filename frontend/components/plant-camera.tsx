"use client"

import { useEffect, useState } from "react"
import { Camera, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function PlantCamera() {
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [lastUpdated, setLastUpdated] = useState<string | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [imageLoaded, setImageLoaded] = useState(false)

    const fetchImage = async () => {
        try {
            const response = await fetch('/api/plant-camera/latest')
            if (!response.ok) {
                setIsLoading(false)
                return
            }
            const data = await response.json()
            if (data.image && data.image !== imageUrl) {
                // Reset loaded state synchronously before updating URL
                setImageLoaded(false)
                setImageUrl(data.image)
                const date = new Date(data.timestamp)
                setLastUpdated(date.toLocaleString())
            }
        } catch (error) {
            console.error("Failed to fetch plant image:", error)
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchImage()
        const interval = setInterval(fetchImage, 30 * 60 * 1000) // Update every 30 minutes
        return () => clearInterval(interval)
    }, [])

    return (
        <Card className="overflow-hidden border-border shadow-md">
            <CardHeader className="flex flex-row items-center justify-between pb-2 bg-card/50 backdrop-blur-sm">
                <CardTitle className="text-lg font-medium flex items-center gap-2">
                    <Camera className="h-5 w-5 text-primary" />
                    プラントカメラ
                </CardTitle>
                <Badge variant="secondary" className="bg-primary/10 text-primary animate-pulse">
                    ライブ
                </Badge>
            </CardHeader>
            <CardContent className="p-0">
                <div className="relative aspect-video bg-muted/30 flex items-center justify-center overflow-hidden">
                    {/* Show loader if fetching API or if image is downloading */}
                    {(isLoading || (imageUrl && !imageLoaded)) && (
                        <div className="flex flex-col items-center gap-3 z-10">
                            <div className="relative">
                                <Loader2 className="h-10 w-10 text-primary animate-spin" />
                                <div className="absolute inset-0 h-10 w-10 border-4 border-primary/20 rounded-full"></div>
                            </div>
                            <p className="text-sm font-medium text-muted-foreground animate-pulse">最新の画像を読み込み中...</p>
                        </div>
                    )}

                    {imageUrl && (
                        <>
                            <img
                                key={imageUrl}
                                src={imageUrl}
                                alt="植物のライブカメラ映像"
                                className={`w-full h-full object-cover transition-all duration-700 ease-in-out ${imageLoaded ? 'scale-100 opacity-100 blur-0' : 'scale-105 opacity-0 blur-sm'}`}
                                onLoad={() => setImageLoaded(true)}
                                onError={() => {
                                    console.error("Image load failed");
                                    setImageLoaded(true); // Stop loader even on error
                                }}
                            />
                            {imageLoaded && lastUpdated && (
                                <div className="absolute bottom-3 left-3 bg-card/80 backdrop-blur-md border border-border/50 rounded-lg px-3 py-1.5 text-sm shadow-lg transform transition-all duration-500 animate-in fade-in slide-in-from-bottom-2">
                                    <span className="text-muted-foreground mr-2 font-medium">最終更新:</span>
                                    <span className="font-semibold">{lastUpdated}</span>
                                </div>
                            )}
                        </>
                    )}

                    {!isLoading && !imageUrl && (
                        <div className="flex flex-col items-center gap-3 text-muted-foreground">
                            <div className="p-4 rounded-full bg-muted">
                                <Camera className="h-8 w-8 opacity-40" />
                            </div>
                            <p className="text-sm font-medium">画像が取得できませんでした</p>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    )
}
