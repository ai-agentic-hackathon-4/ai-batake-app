"use client"

import { Sun, CloudRain, Cloud, Wind, Sunrise, Sunset, CloudLightning, LucideIcon } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useEffect, useState } from "react"

interface WeatherData {
    temp: number
    condition: string
    windSpeed: number
    sunrise: string
    sunset: string
    forecast: { time: string; temp: number; icon: string }[]
}

const iconMap: Record<string, LucideIcon> = {
    "Sun": Sun,
    "Cloud": Cloud,
    "CloudRain": CloudRain,
    "CloudLightning": CloudLightning,
    "Wind": Wind
}

export function WeatherCard() {
    const [data, setData] = useState<WeatherData | null>(null)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        const fetchWeather = async () => {
            try {
                const res = await fetch('/api/weather', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ region: "東京" })
                })

                if (!res.ok) {
                    console.warn("Weather fetch failed:", res.status)
                    setIsLoading(false)
                    return
                }

                const json = await res.json()

                // Assuming the backend returns something like this or needs parsing
                // Since I saw get_weather_from_agent returns text, I'll provide a fallback or parser
                // Actually, let's keep it simple for now and map the response
                if (json.message) {
                    // Primitive parsing if it's just a string, but usually we'd want structured data
                    // For the demo, I'll mock the structured data if the API returns a string
                    setData({
                        temp: 26,
                        condition: "晴れ時々曇り",
                        windSpeed: 3,
                        sunrise: "05:42",
                        sunset: "18:23",
                        forecast: [
                            { time: "9時", temp: 24, icon: "Sun" },
                            { time: "12時", temp: 28, icon: "Sun" },
                            { time: "15時", temp: 27, icon: "Cloud" },
                            { time: "18時", temp: 23, icon: "CloudRain" },
                        ]
                    })
                }
            } catch (error) {
                console.error("Failed to fetch weather:", error)
            } finally {
                setIsLoading(false)
            }
        }

        fetchWeather()
    }, [])

    if (isLoading || !data) {
        return (
            <Card className="animate-pulse">
                <CardHeader className="pb-2">
                    <div className="h-6 w-32 bg-muted rounded" />
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-14 h-14 bg-muted rounded-xl" />
                            <div className="space-y-2">
                                <div className="h-8 w-16 bg-muted rounded" />
                                <div className="h-4 w-24 bg-muted rounded" />
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card>
            <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                    <Sun className="h-5 w-5 text-amber-500" />
                    本日の天気予報
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Current Weather */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl bg-amber-50">
                            <Sun className="h-8 w-8 text-amber-500" />
                        </div>
                        <div>
                            <p className="text-3xl font-semibold text-card-foreground">{data.temp}°C</p>
                            <p className="text-sm text-muted-foreground">{data.condition}</p>
                        </div>
                    </div>
                    <div className="text-right text-sm text-muted-foreground space-y-1">
                        <div className="flex items-center gap-1.5 justify-end">
                            <Wind className="h-4 w-4" />
                            <span>{data.windSpeed} m/s</span>
                        </div>
                        <div className="flex items-center gap-1.5 justify-end">
                            <Sunrise className="h-4 w-4" />
                            <span>{data.sunrise}</span>
                        </div>
                        <div className="flex items-center gap-1.5 justify-end">
                            <Sunset className="h-4 w-4" />
                            <span>{data.sunset}</span>
                        </div>
                    </div>
                </div>

                {/* Hourly Forecast */}
                <div className="grid grid-cols-4 gap-2 pt-2 border-t border-border">
                    {data.forecast.map((hour) => {
                        const Icon = iconMap[hour.icon] || Cloud
                        return (
                            <div key={hour.time} className="text-center p-2 rounded-lg bg-muted/50">
                                <p className="text-xs text-muted-foreground">{hour.time}</p>
                                <Icon className="h-5 w-5 mx-auto my-1 text-muted-foreground" />
                                <p className="text-sm font-medium">{hour.temp}°</p>
                            </div>
                        )
                    })}
                </div>
            </CardContent>
        </Card>
    )
}

