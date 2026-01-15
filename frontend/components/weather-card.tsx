import { Sun, CloudRain, Cloud, Wind, Sunrise, Sunset } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const hourlyForecast = [
    { time: "9時", temp: 24, icon: Sun },
    { time: "12時", temp: 28, icon: Sun },
    { time: "15時", temp: 27, icon: Cloud },
    { time: "18時", temp: 23, icon: CloudRain },
]

export function WeatherCard() {
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
                            <p className="text-3xl font-semibold text-card-foreground">26°C</p>
                            <p className="text-sm text-muted-foreground">晴れ時々曇り</p>
                        </div>
                    </div>
                    <div className="text-right text-sm text-muted-foreground space-y-1">
                        <div className="flex items-center gap-1.5 justify-end">
                            <Wind className="h-4 w-4" />
                            <span>3 m/s</span>
                        </div>
                        <div className="flex items-center gap-1.5 justify-end">
                            <Sunrise className="h-4 w-4" />
                            <span>5:42</span>
                        </div>
                        <div className="flex items-center gap-1.5 justify-end">
                            <Sunset className="h-4 w-4" />
                            <span>18:23</span>
                        </div>
                    </div>
                </div>

                {/* Hourly Forecast */}
                <div className="grid grid-cols-4 gap-2 pt-2 border-t border-border">
                    {hourlyForecast.map((hour) => (
                        <div key={hour.time} className="text-center p-2 rounded-lg bg-muted/50">
                            <p className="text-xs text-muted-foreground">{hour.time}</p>
                            <hour.icon className="h-5 w-5 mx-auto my-1 text-muted-foreground" />
                            <p className="text-sm font-medium">{hour.temp}°</p>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}
