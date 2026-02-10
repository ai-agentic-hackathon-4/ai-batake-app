"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { Activity } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

export function EnvironmentChart() {
    const [chartData, setChartData] = useState<{
        timestamp: number;
        temperature: number;
        humidity: number;
        soil_moisture: number;
        illuminance: number;
    }[]>([])
    const [timeRange, setTimeRange] = useState("24")
    const [now, setNow] = useState<number>(Date.now() / 1000)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch(`/api/sensor-history?hours=${timeRange}`)
                const json = await res.json()
                if (json.data) {
                    const formattedData = json.data.map((item: any) => ({
                        timestamp: item.unix_timestamp,
                        temperature: item.temperature,
                        humidity: item.humidity,
                        soil_moisture: item.soil_moisture || 0,
                        illuminance: item.illuminance || 0
                    }))
                    setChartData(formattedData)
                    setNow(Date.now() / 1000)
                }
            } catch (error) {
                console.error("Failed to fetch sensor data:", error)
            } finally {
                setIsLoading(false)
            }
        }

        fetchData()
        // Refresh every minute
        const interval = setInterval(() => {
            fetchData()
        }, 60000)
        return () => clearInterval(interval)
    }, [timeRange])

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

    if (isLoading && chartData.length === 0) {
        return (
            <Card className="animate-pulse">
                <CardHeader className="flex flex-row items-center justify-between pb-4">
                    <div className="flex items-center gap-2">
                        <Activity className="h-5 w-5 text-muted" />
                        <div className="h-6 w-32 bg-muted rounded" />
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="h-[280px] w-full bg-muted/10 rounded-lg flex items-center justify-center">
                        <Activity className="h-10 w-10 text-muted opacity-20" />
                    </div>
                </CardContent>
            </Card>
        )
    }

    return (
        <div className="space-y-4">
            {/* Control Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-primary" />
                    <h2 className="text-xl font-semibold">環境データ履歴</h2>
                </div>
                <Select value={timeRange} onValueChange={setTimeRange}>
                    <SelectTrigger className="w-[140px]">
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
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* 温湿度 Chart */}
                <Card className="lg:col-span-2">
                    <CardHeader className="pb-4">
                        <CardTitle className="text-lg font-medium">気温・湿度</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px]">
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
                                        stroke="#ef4444"
                                        strokeWidth={2}
                                        dot={false}
                                        activeDot={{ r: 4, fill: "#ef4444" }}
                                    />
                                    <Line
                                        yAxisId="humidity"
                                        type="monotone"
                                        dataKey="humidity"
                                        stroke="#3b82f6"
                                        strokeWidth={2}
                                        dot={false}
                                        activeDot={{ r: 4, fill: "#3b82f6" }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* 土壌水分 Chart */}
                <Card>
                    <CardHeader className="pb-4">
                        <CardTitle className="text-lg font-medium">土壌水分</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[250px]">
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
                                        stroke="hsl(var(--muted-foreground))"
                                        fontSize={12}
                                        tickLine={false}
                                        domain={[0, 100]}
                                        ticks={[0, 25, 50, 75, 100]}
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
                                        formatter={(value: number) => [`${value}%`, "土壌水分"]}
                                    />
                                    <Legend formatter={() => "土壌水分 (%)"} />
                                    <Line
                                        type="monotone"
                                        dataKey="soil_moisture"
                                        stroke="#10b981"
                                        strokeWidth={2}
                                        dot={false}
                                        activeDot={{ r: 4, fill: "#10b981" }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* 照度 Chart */}
                <Card>
                    <CardHeader className="pb-4">
                        <CardTitle className="text-lg font-medium">照度</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[250px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData} margin={{ top: 5, right: 10, left: 15, bottom: 5 }}>
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
                                        stroke="hsl(var(--muted-foreground))"
                                        fontSize={12}
                                        tickLine={false}
                                        width={45}
                                        tickFormatter={(value) => `${value}lx`}
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
                                        formatter={(value: number) => [`${value} lx`, "照度"]}
                                    />
                                    <Legend formatter={() => "照度 (lx)"} />
                                    <Line
                                        type="monotone"
                                        dataKey="illuminance"
                                        stroke="#facc15"
                                        strokeWidth={2}
                                        dot={false}
                                        activeDot={{ r: 4, fill: "#facc15" }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
