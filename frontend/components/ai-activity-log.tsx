import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Bot, Droplets, AlertTriangle, Eye, Sun, Wind, type LucideIcon } from "lucide-react"

interface Activity {
    id: number
    time: string
    action: string
    type: "action" | "warning" | "alert" | "info"
    icon: LucideIcon
}

const activities: Activity[] = [
    {
        id: 1,
        time: "18:00",
        action: "葉の異常を画像から検出",
        type: "alert",
        icon: Eye,
    },
    {
        id: 2,
        time: "16:45",
        action: "換気システムを起動",
        type: "action",
        icon: Wind,
    },
    {
        id: 3,
        time: "14:10",
        action: "乾燥状態を検出",
        type: "warning",
        icon: AlertTriangle,
    },
    {
        id: 4,
        time: "12:30",
        action: "遮光カーテンを調整",
        type: "action",
        icon: Sun,
    },
    {
        id: 5,
        time: "10:32",
        action: "水やりを実行",
        type: "action",
        icon: Droplets,
    },
    {
        id: 6,
        time: "08:00",
        action: "朝の環境チェック完了",
        type: "info",
        icon: Bot,
    },
]

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
    return (
        <Card>
            <CardHeader className="flex flex-row items-center gap-2 pb-4">
                <Bot className="h-5 w-5 text-primary" />
                <CardTitle className="text-lg font-medium">AIアクティビティログ</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
                {activities.map((activity) => (
                    <div
                        key={activity.id}
                        className="flex items-start gap-3 p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors"
                    >
                        <div className={`p-2 rounded-full ${typeStyles[activity.type as keyof typeof typeStyles]}`}>
                            <activity.icon className="h-4 w-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-card-foreground">{activity.action}</p>
                            <p className="text-xs text-muted-foreground mt-0.5">{activity.time}</p>
                        </div>
                        <Badge variant="outline" className={`shrink-0 text-xs ${typeStyles[activity.type as keyof typeof typeStyles]}`}>
                            {typeLabels[activity.type as keyof typeof typeLabels]}
                        </Badge>
                    </div>
                ))}
            </CardContent>
        </Card>
    )
}
