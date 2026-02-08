"use client"

import { useEffect, useState } from "react"
import { Thermometer, Droplets, Leaf, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { PlantCamera } from "@/components/plant-camera"
import { MetricCard } from "@/components/metric-card"
import { EnvironmentChart } from "@/components/environment-chart"
import { AIActivityLog } from "@/components/ai-activity-log"
import { WeatherCard } from "@/components/weather-card"
import { GrowthStageCard } from "@/components/growth-stage-card"

export default function Dashboard() {
    const [sensorData, setSensorData] = useState<{ temperature: number | string; humidity: number | string }>({
        temperature: "--",
        humidity: "--"
    })

    useEffect(() => {
        const fetchSensorData = async () => {
            try {
                const res = await fetch('/api/sensors/latest')
                const data = await res.json()
                if (data && data.temperature !== undefined) {
                    setSensorData({
                        temperature: data.temperature,
                        humidity: data.humidity
                    })
                }
            } catch (error) {
                console.error("Failed to fetch latest sensor data:", error)
            }
        }

        fetchSensorData()
        const interval = setInterval(fetchSensorData, 60000) // Update every minute
        return () => clearInterval(interval)
    }, [])

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b border-border bg-card">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center gap-3">
                        <Link href="/" className="mr-2 p-1 hover:bg-accent rounded-full transition-colors">
                            <ArrowLeft className="h-5 w-5 text-muted-foreground" />
                        </Link>
                        <div className="p-2 rounded-lg bg-primary/10">
                            <Leaf className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold text-card-foreground">Smart Farm ダッシュボード</h1>
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
    )
}
