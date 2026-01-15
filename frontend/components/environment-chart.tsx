"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { Activity } from "lucide-react"

const data = [
    { time: "00:00", temperature: 22, humidity: 65 },
    { time: "02:00", temperature: 21, humidity: 68 },
    { time: "04:00", temperature: 20, humidity: 70 },
    { time: "06:00", temperature: 21, humidity: 72 },
    { time: "08:00", temperature: 23, humidity: 68 },
    { time: "10:00", temperature: 25, humidity: 62 },
    { time: "12:00", temperature: 27, humidity: 55 },
    { time: "14:00", temperature: 28, humidity: 52 },
    { time: "16:00", temperature: 26, humidity: 58 },
    { time: "18:00", temperature: 24, humidity: 63 },
    { time: "20:00", temperature: 23, humidity: 66 },
    { time: "22:00", temperature: 22, humidity: 68 },
]

export function EnvironmentChart() {
    return (
        <Card>
            <CardHeader className="flex flex-row items-center gap-2 pb-4">
                <Activity className="h-5 w-5 text-primary" />
                <CardTitle className="text-lg font-medium">環境データ（24時間）</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="h-[280px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                            <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} />
                            <YAxis
                                yAxisId="temp"
                                stroke="hsl(var(--muted-foreground))"
                                fontSize={12}
                                tickLine={false}
                                domain={[15, 35]}
                                tickFormatter={(value) => `${value}°`}
                            />
                            <YAxis
                                yAxisId="humidity"
                                orientation="right"
                                stroke="hsl(var(--muted-foreground))"
                                fontSize={12}
                                tickLine={false}
                                domain={[40, 80]}
                                tickFormatter={(value) => `${value}%`}
                            />
                            <Tooltip
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
