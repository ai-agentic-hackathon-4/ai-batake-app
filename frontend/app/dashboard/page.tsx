"use client"

import { useEffect, useState } from "react"
import { Thermometer, Droplets, Leaf, ArrowLeft, Sun, Sprout } from "lucide-react"
import Link from "next/link"
import { PlantCamera } from "@/components/plant-camera"
import { MetricCard } from "@/components/metric-card"
import { EnvironmentChart } from "@/components/environment-chart"
import { AIActivityLog } from "@/components/ai-activity-log"
import { GrowthStageCard } from "@/components/growth-stage-card"
import { LoadingOverlay } from "@/components/loading-overlay"
import { CharacterMessage } from "@/components/character-message"

export default function Dashboard() {
    const [isLoading, setIsLoading] = useState(true)
    const [sensorData, setSensorData] = useState<{
        temperature: number | string;
        humidity: number | string;
        soil_moisture: number | string;
        illuminance: number | string;
    }>({
        temperature: "--",
        humidity: "--",
        soil_moisture: "--",
        illuminance: "--"
    })

    useEffect(() => {
        const fetchInitialData = async () => {
            try {
                // We only need the latest sensor data for the top-level MetricCards
                // Other components (PlantCamera, EnvironmentChart, AIActivityLog) fetch their own data
                const res = await fetch('/api/sensors/latest')
                if (res.ok) {
                    const data = await res.json()
                    if (data && data.temperature !== undefined) {
                        setSensorData({
                            temperature: data.temperature,
                            humidity: data.humidity,
                            soil_moisture: data.soil_moisture ?? "--",
                            illuminance: data.illuminance !== undefined ? Math.round(Number(data.illuminance)) : "--"
                        })
                    }
                }
            } catch (error) {
                console.error("Failed to fetch initial sensor data:", error)
            } finally {
                // Hide loading screen as soon as we have the basic stats
                setIsLoading(false)
            }
        }

        fetchInitialData()

        // Background refresh interval for sensors (keep existing logic)
        const interval = setInterval(async () => {
            try {
                const res = await fetch('/api/sensors/latest')
                const data = await res.json()
                if (data && data.temperature !== undefined) {
                    setSensorData({
                        temperature: data.temperature,
                        humidity: data.humidity,
                        soil_moisture: data.soil_moisture ?? "--",
                        illuminance: data.illuminance !== undefined ? Math.round(Number(data.illuminance)) : "--"
                    })
                }
            } catch (e) {
                console.error("BG fetch failed:", e)
            }
        }, 60000)

        return () => clearInterval(interval)
    }, [])

    return (
        <>
            <LoadingOverlay isVisible={isLoading} />
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

                    {/* Character Message and Growth Stage Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <CharacterMessage />
                        <GrowthStageCard />
                    </div>


                    {/* Metrics Section */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <MetricCard title="現在の気温" value={String(sensorData.temperature)} unit="°C" icon={Thermometer} status="normal" />
                        <MetricCard title="現在の湿度" value={String(sensorData.humidity)} unit="%" icon={Droplets} status="normal" />
                        <MetricCard title="土壌水分" value={String(sensorData.soil_moisture)} unit="%" icon={Sprout} status="normal" />
                        <MetricCard title="現在の照度" value={String(sensorData.illuminance)} unit="lx" icon={Sun} status="normal" />
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
        </>
    )
}

