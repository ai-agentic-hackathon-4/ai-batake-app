import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Bot, Droplets, AlertTriangle, Eye, Sun, Wind, type LucideIcon, Info, ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"

interface LogItem {
    id: string
    action: string
    type: "action" | "warning" | "alert" | "info"
    icon: LucideIcon
}

interface LogGroup {
    id: string | number
    time: string
    items: LogItem[]
}

const typeStyles = {
    action: "bg-primary/10 text-primary border-primary/20",
    warning: "bg-chart-2/10 text-chart-2 border-chart-2/20",
    alert: "bg-destructive/10 text-destructive border-destructive/20",
    info: "bg-muted text-muted-foreground border-muted",
}

const typeLabels = {
    action: "実行",
    warning: "警告",
    alert: "アラート",
    info: "情報",
}

export function AIActivityLog() {
    const [groups, setGroups] = useState<LogGroup[]>([])
    const [isExpanded, setIsExpanded] = useState(false)

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const res = await fetch('/api/agent-logs')
                const data = await res.json()

                if (data && data.logs) {
                    const formattedGroups: LogGroup[] = data.logs.map((log: any) => {
                        const logData = log.data || {}
                        const items: LogItem[] = []

                        // 1. Process Operations
                        if (logData.operation) {
                            Object.entries(logData.operation).forEach(([device, op]: [string, any]) => {
                                const action = op.action || ""

                                let type: LogItem['type'] = 'info'
                                let icon = Bot

                                if (device.includes("エアコン") || device.includes("ファン") || device.includes("空調")) icon = Wind
                                else if (device.includes("ライト") || device.includes("照明") || device.includes("LED")) icon = Sun
                                else if (device.includes("ポンプ") || device.includes("水")) icon = Droplets
                                else if (device.includes("カメラ")) icon = Eye
                                else icon = Bot

                                // IMPORTANT: Only show "Active" operations (ON/OFF) or status changes
                                if (action.includes("ON") || action.includes("起動") || action.includes("変更")) {
                                    type = 'action'
                                } else if (action.includes("OFF") || action.includes("停止")) {
                                    type = 'action'
                                } else if (action.includes("現状維持")) {
                                    type = 'info'
                                }

                                items.push({
                                    id: (log.id || "gen") + "-" + device,
                                    action: `[${device}] ${action}`,
                                    type: type,
                                    icon: icon
                                })
                            })
                        }

                        // 2. Process Comments (Only Alerts/Warnings)
                        const comment = logData.comment || ""
                        if (comment.includes("異常") || comment.includes("エラー")) {
                            items.push({
                                id: (log.id || "gen") + "-alert",
                                action: comment,
                                type: 'alert',
                                icon: AlertTriangle
                            })
                        } else if (comment.includes("警告") || comment.includes("注意")) {
                            items.push({
                                id: (log.id || "gen") + "-warn",
                                action: comment,
                                type: 'warning',
                                icon: AlertTriangle
                            })
                        }

                        // Format Time
                        let timeStr = "--:--"
                        if (log.timestamp) {
                            try {
                                const date = new Date(log.timestamp)
                                timeStr = date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })
                            } catch (e) {
                                timeStr = String(log.timestamp)
                            }
                        }

                        return {
                            id: log.id || Math.random(),
                            time: timeStr,
                            items: items
                        }
                    }).filter((group: LogGroup) => group.items.length > 0)

                    setGroups(formattedGroups)
                }
            } catch (error) {
                console.error("Failed to fetch agent logs:", error)
            }
        }

        fetchLogs()
        const interval = setInterval(fetchLogs, 30000)
        return () => clearInterval(interval)
    }, [])

    return (
        <Card className="flex flex-col h-full">
            <CardHeader className="flex flex-row items-center gap-2 pb-4 shrink-0">
                <Bot className="h-5 w-5 text-primary" />
                <CardTitle className="text-lg font-medium">AIアクティビティログ</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 relative">
                <div
                    className={`space-y-4 overflow-hidden transition-all duration-300 pl-2 pt-2 ${isExpanded ? "" : "max-h-[400px]"
                        }`}
                >
                    {groups.length === 0 ? (
                        <div className="text-center text-muted-foreground py-4">
                            ログはありません
                        </div>
                    ) : (
                        groups.map((group) => (
                            <div key={group.id} className="relative pl-4 border-l-2 border-muted pb-4 last:pb-0 last:border-0">
                                {/* Time Badge / Marker */}
                                <div className="absolute -left-[9px] top-0 bg-background p-0.5">
                                    <div className="h-4 w-4 rounded-full border-2 border-primary bg-background" />
                                </div>
                                <div className="mb-2 -mt-1">
                                    <span className="text-xs font-medium text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                                        {group.time}
                                    </span>
                                </div>

                                {/* Items Group */}
                                <div className="space-y-2">
                                    {group.items.map((item) => (
                                        <div
                                            key={item.id}
                                            className="flex items-center gap-3 p-2.5 rounded-lg bg-secondary/30 hover:bg-secondary/60 transition-colors"
                                        >
                                            <div className={`p-1.5 rounded-full shrink-0 ${typeStyles[item.type]}`}>
                                                <item.icon className="h-3.5 w-3.5" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm text-card-foreground leading-tight">{item.action}</p>
                                            </div>
                                            <Badge variant="outline" className={`shrink-0 text-[10px] px-1.5 py-0 h-5 ${typeStyles[item.type]}`}>
                                                {typeLabels[item.type]}
                                            </Badge>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Gradient Overlay & Button */}
                {!isExpanded && groups.length > 0 && (
                    <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-background via-background/80 to-transparent flex items-end justify-center pb-0 pointer-events-none">
                    </div>
                )}

                {groups.length > 3 && (
                    <div className={`flex justify-center mt-4 ${!isExpanded ? "absolute bottom-2 left-0 right-0 z-10" : ""}`}>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setIsExpanded(!isExpanded)}
                            className="bg-card hover:bg-secondary shadow-sm"
                        >
                            {isExpanded ? (
                                <>
                                    <ChevronUp className="mr-2 h-4 w-4" />
                                    閉じる
                                </>
                            ) : (
                                <>
                                    <ChevronDown className="mr-2 h-4 w-4" />
                                    さらに表示
                                </>
                            )}
                        </Button>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
