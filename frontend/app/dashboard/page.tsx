"use client"

import { useEffect, useState } from "react"
import { Thermometer, Droplets, Leaf } from "lucide-react"
import { PlantCamera } from "@/components/plant-camera"
import { MetricCard } from "@/components/metric-card"
import { EnvironmentChart } from "@/components/environment-chart"
import { AIActivityLog } from "@/components/ai-activity-log"
import { WeatherCard } from "@/components/weather-card"
import { GrowthStageCard } from "@/components/growth-stage-card"
import { LoadingOverlay } from "@/components/loading-overlay"

export default function Dashboard() {
    const [isLoading, setIsLoading] = useState(true)
    const [sensorData, setSensorData] = useState<{ temperature: number | string; humidity: number | string }>({
        temperature: "--",
        humidity: "--"
    })

    // Track loading status of individual components if needed, or just wait for all initial fetches
    const [isDataLoaded, setIsDataLoaded] = useState({
        sensors: false,
        camera: false,
        logs: false,
        weather: false
    })

    useEffect(() => {
        const fetchAllData = async () => {
            const safeFetch = async (url: string, options?: RequestInit) => {
                try {
                    const res = await fetch(url, options)
                    if (!res.ok) {
                        console.warn(`Fetch to ${url} failed with status: ${res.status}`)
                        return null
                    }
                    const text = await res.text()
                    try {
                        return JSON.parse(text)
                    } catch (e) {
                        console.error(`Failed to parse JSON for ${url}:`, text.slice(0, 100))
                        return null
                    }
                } catch (e) {
                    console.error(`Network error fetching ${url}:`, e)
                    return null
                }
            }

            try {
                // We'll perform essential fetches here to gate the loading screen
                const sensorPromise = safeFetch('/api/sensors/latest')
                const cameraPromise = safeFetch('/api/plant-camera/latest')
                const logsPromise = safeFetch('/api/agent-logs')
                const historyPromise = safeFetch('/api/sensor-history?hours=24')
                const weatherPromise = safeFetch('/api/weather', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ region: "東京" })
                })

                const [sensors, camera, logs, history, weather] = await Promise.all([
                    sensorPromise,
                    cameraPromise,
                    logsPromise,
                    historyPromise,
                    weatherPromise
                ])

                if (sensors && sensors.temperature !== undefined) {
                    setSensorData({
                        temperature: sensors.temperature,
                        humidity: sensors.humidity
                    })
                }

                // Mark everything as loaded
                setIsDataLoaded({
                    sensors: true,
                    camera: true,
                    logs: true,
                    weather: true
                })

                // Keep the loading screen for a tiny bit longer for a smooth transition
                setTimeout(() => setIsLoading(false), 500)
            } catch (error) {
                console.error("Failed to fetch initial dashboard data:", error)
                // Even on error, we should probably hide the loader eventually
                setIsLoading(false)
            }
        }

        fetchAllData()

        // Background refresh interval for sensors (keep existing logic)
        const interval = setInterval(async () => {
            try {
                const res = await fetch('/api/sensors/latest')
                const data = await res.json()
                if (data && data.temperature !== undefined) {
                    setSensorData({
                        temperature: data.temperature,
                        humidity: data.humidity
                    })
                }
            } catch (e) {
                console.error("BG fetch failed:", e)
            }
        }, 60000)

        return () => clearInterval(interval)
    }, [])

    return (
        <div className="min-h-screen bg-background relative">
            <LoadingOverlay isVisible={isLoading} />

            <div className={`transition-all duration-700 ${isLoading ? "opacity-0 blur-sm scale-95" : "opacity-100 blur-0 scale-100"}`}>
                {/* Header */}
                <header className="border-b border-border bg-card sticky top-0 z-10 backdrop-blur-md bg-card/80">
                    <div className="max-w-7xl mx-auto px-6 py-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-primary/10">
                                <Leaf className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                                <h1 className="text-xl font-semibold text-card-foreground">Smart Farm Dashboard</h1>
                                <p className="text-sm text-muted-foreground">AI栽培管理システム</p>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Main Content */}
                <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
                    {/* Plant Camera Section */}
                    <PlantCamera />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <WeatherCard />
                        <GrowthStageCard />
                    </div>

                    {/* Metrics Section */}
                    <div className="grid grid-cols-2 gap-4">
                        <MetricCard title="現在の気温" value={String(sensorData.temperature)} unit="°C" icon={Thermometer} status="normal" />
                        <MetricCard title="現在の湿度" value={String(sensorData.humidity)} unit="%" icon={Droplets} status="normal" />
                    </div>

                    {/* Chart Section */}
                    <EnvironmentChart />

                    {/* AI Activity Log Section */}
                    <AIActivityLog />
                </main>

                {/* Footer */}
                <footer className="border-t border-border bg-card mt-8">
                    <div className="max-w-7xl mx-auto px-6 py-4">
                        <p className="text-sm text-muted-foreground text-center">© 2025 Smart Farm AI - ハッカソンデモ</p>
                    </div>
                </footer>
            </div>
        </div>
    )
}

