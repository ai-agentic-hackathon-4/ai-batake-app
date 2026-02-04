import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Bot, Droplets, AlertTriangle, Eye, Sun, Wind, type LucideIcon, Info } from "lucide-react"

interface Activity {
    id: string | number
    time: string
    action: string
    type: "action" | "warning" | "alert" | "info"
    icon: LucideIcon
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
    const [activities, setActivities] = useState<Activity[]>([])

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const res = await fetch('/api/agent-logs')
                const data = await res.json()

                if (data && data.logs) {
                    const formattedLogs: Activity[] = data.logs.map((log: any) => {
                        const logData = log.data || {}

                        // Determine type/icon
                        let type: Activity['type'] = 'info'
                        let icon = Bot

                        // Check distinct error log format first (if any)
                        // But mostly we have agent periodic logs

                        // Analyze content for type/icon
                        // Combine comment and logs for keyword search
                        const fullText = (logData.comment || "") + (logData.logs?.join(" ") || "") + (JSON.stringify(logData.operation || ""));

                        if (fullText.includes("異常") || fullText.includes("エラー") || fullText.includes("Error")) {
                            type = 'alert'
                            icon = AlertTriangle
                        } else if (fullText.includes("警告") || fullText.includes("Warning") || fullText.includes("乾燥")) {
                            type = 'warning'
                            icon = AlertTriangle
                        } else if (logData.operation && Object.keys(logData.operation).length > 0) {
                            // If there are operations, mark as action
                            const ops = logData.operation;
                            let hasRealAction = false;
                            for (const key in ops) {
                                if (ops[key].action && !ops[key].action.includes("現状維持") && !ops[key].action.includes("OFF")) {
                                    hasRealAction = true;
                                }
                            }
                            if (hasRealAction) {
                                type = 'action'
                                icon = Bot
                            }
                        }

                        // Icon refinement
                        if (fullText.includes("水")) icon = Droplets
                        if (fullText.includes("光") || fullText.includes("ライト") || fullText.includes("照明")) icon = Sun
                        if (fullText.includes("風") || fullText.includes("ファン") || fullText.includes("エアコン")) icon = Wind
                        if (fullText.includes("画像") || fullText.includes("カメラ") || fullText.includes("芽")) icon = Eye


                        // Action Text: Use comment or summary of operations
                        let actionText = logData.comment || "定期モニタリング完了"

                        // If there is a specific operation, mention it?
                        // But comment is usually good.
                        // Let's truncate comment if too long for the list
                        if (actionText.length > 40) {
                            actionText = actionText.substring(0, 40) + "..."
                        }

                        // Format time
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
                            action: actionText,
                            type: type,
                            icon: icon
                        }
                    })
                    setActivities(formattedLogs)
                }
            } catch (error) {
                console.error("Failed to fetch agent logs:", error)
            }
        }

        fetchLogs()
        const interval = setInterval(fetchLogs, 30000) // Refresh every 30s
        return () => clearInterval(interval)
    }, [])

    return (
        <Card>
            <CardHeader className="flex flex-row items-center gap-2 pb-4">
                <Bot className="h-5 w-5 text-primary" />
                <CardTitle className="text-lg font-medium">AIアクティビティログ</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
                {activities.length === 0 ? (
                    <div className="text-center text-muted-foreground py-4">
                        ログはありません
                    </div>
                ) : (
                    activities.map((activity) => (
                        <div
                            key={activity.id}
                            className="flex items-start gap-3 p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors"
                        >
                            <div className={`p-2 rounded-full ${typeStyles[activity.type]}`}>
                                <activity.icon className="h-4 w-4" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-card-foreground">{activity.action}</p>
                                <p className="text-xs text-muted-foreground mt-0.5">{activity.time}</p>
                            </div>
                            <Badge variant="outline" className={`shrink-0 text-xs ${typeStyles[activity.type]}`}>
                                {typeLabels[activity.type]}
                            </Badge>
                        </div>
                    ))
                )}
            </CardContent>
        </Card>
    )
}
