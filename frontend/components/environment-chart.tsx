"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { Activity } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

export function EnvironmentChart() {
    const [chartData, setChartData] = useState<{ timestamp: number; temperature: number; humidity: number }[]>([])
    const [timeRange, setTimeRange] = useState("24")
    const [now, setNow] = useState<number>(Date.now() / 1000)

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch(`/api/sensor-history?hours=${timeRange}`)
                const json = await res.json()
                if (json.data) {
                    const formattedData = json.data.map((item: any) => ({
                        timestamp: item.unix_timestamp, // Keep as number (seconds)
                        temperature: item.temperature,
                        humidity: item.humidity
                    }))
                    setChartData(formattedData)
                    setNow(Date.now() / 1000)
                }
            } catch (error) {
                console.error("Failed to fetch sensor data:", error)
            }
        }

        fetchData()
        // Refresh every minute
        const interval = setInterval(() => {
            fetchData()
        }, 60000)
        return () => clearInterval(interval)
    }, [timeRange]) // Re-fetch when timeRange changes

    // Calculate time domain
    const rangeInSeconds = parseInt(timeRange) * 3600
    const minTime = now - rangeInSeconds
    const maxTime = now

    // Determine tick interval based on range
    let tickInterval = 3600 * 4 // Default 4 hours
    if (timeRange === "6") tickInterval = 3600 // 1 hour
    else if (timeRange === "12") tickInterval = 3600 * 2 // 2 hours
    else if (timeRange === "24") tickInterval = 3600 * 4 // 4 hours
    else if (timeRange === "72") tickInterval = 3600 * 12 // 12 hours
    else if (timeRange === "168") tickInterval = 3600 * 24 // 24 hours

    // Generate accurate time ticks
    const timeTicks = []
    let t = Math.ceil(minTime / tickInterval) * tickInterval
    while (t <= maxTime) {
        // Adjust to be "nice" timestamps (e.g. on the hour)
        // For larger intervals, align to 00:00 or 12:00
        const d = new Date(t * 1000)

        let aligned = false
        if (timeRange === "6" || timeRange === "12") {
            // Align to hour
            if (d.getMinutes() === 0 && d.getHours() % (tickInterval / 3600) === 0) aligned = true
        } else if (timeRange === "24") {
            if (d.getMinutes() === 0 && d.getHours() % 4 === 0) aligned = true
        } else if (timeRange === "72") {
            if (d.getMinutes() === 0 && d.getHours() % 12 === 0) aligned = true
        } else if (timeRange === "168") {
            if (d.getMinutes() === 0 && d.getHours() === 0) aligned = true
        }

        if (timeTicks.length === 0 || aligned) {
            // Simply add t if it matches interval logic loosely or exact alignment
            // The logic above is a bit complex for simple loop, let's simplify:
            // We can just trust the loop increment if we start correctly.
            // Start t at the first multiple after minTime?
        }

        timeTicks.push(t)
        t += tickInterval
    }

    // Better tick generation:
    const simpleTicks = []
    const startTick = Math.ceil(minTime / tickInterval) * tickInterval
    for (let current = startTick; current <= maxTime; current += tickInterval) {
        simpleTicks.push(current)
    }


    const formatXAxis = (unixTime: number) => {
        const date = new Date(unixTime * 1000)
        if (parseInt(timeRange) > 24) {
            return date.toLocaleDateString([], { month: 'numeric', day: 'numeric' }) + " " + date.getHours() + "時"
        }
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-4">
                <div className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-primary" />
                    <CardTitle className="text-lg font-medium">環境データ</CardTitle>
                </div>
                <Select value={timeRange} onValueChange={setTimeRange}>
                    <SelectTrigger className="w-[120px]">
                        <SelectValue placeholder="期間を選択" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="6">直近6時間</SelectItem>
                        <SelectItem value="12">直近12時間</SelectItem>
                        <SelectItem value="24">直近24時間</SelectItem>
                        <SelectItem value="72">直近3日間</SelectItem>
                        <SelectItem value="168">直近7日間</SelectItem>
                    </SelectContent>
                </Select>
            </CardHeader>
            <CardContent>
                <div className="h-[280px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                            <XAxis
                                dataKey="timestamp"
                                type="number"
                                domain={[minTime, maxTime]}
                                ticks={simpleTicks}
                                stroke="hsl(var(--muted-foreground))"
                                fontSize={12}
                                tickLine={false}
                                tickFormatter={formatXAxis}
                            />
                            <YAxis
                                yAxisId="temp"
                                stroke="hsl(var(--muted-foreground))"
                                fontSize={12}
                                tickLine={false}
                                domain={[0, 40]}
                                ticks={[0, 10, 20, 30, 40]}
                                tickFormatter={(value) => `${value}°`}
                            />
                            <YAxis
                                yAxisId="humidity"
                                orientation="right"
                                stroke="hsl(var(--muted-foreground))"
                                fontSize={12}
                                tickLine={false}
                                domain={[0, 100]}
                                ticks={[0, 20, 40, 60, 80, 100]}
                                tickFormatter={(value) => `${value}%`}
                            />
                            <Tooltip
                                labelFormatter={(label) => {
                                    return new Date(label * 1000).toLocaleString([], {
                                        month: 'numeric',
                                        day: 'numeric',
                                        hour: '2-digit',
                                        minute: '2-digit'
                                    })
                                }}
                                contentStyle={{
                                    backgroundColor: "hsl(var(--card))",
                                    border: "1px solid hsl(var(--border))",
                                    borderRadius: "8px",
                                    fontSize: "12px",
                                }}
                                formatter={(value: number, name: string) => [
                                    name === "temperature" ? `${value}°C` : `${value}%`,
                                    name === "temperature" ? "気温" : "湿度",
                                ]}
                            />
                            <Legend formatter={(value) => (value === "temperature" ? "気温 (°C)" : "湿度 (%)")} />
                            <Line
                                yAxisId="temp"
                                type="monotone"
                                dataKey="temperature"
                                stroke="#f97316"
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 4, fill: "hsl(var(--primary))" }}
                            />
                            <Line
                                yAxisId="humidity"
                                type="monotone"
                                dataKey="humidity"
                                stroke="#0ea5e9"
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 4, fill: "hsl(var(--chart-2))" }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    )
}
