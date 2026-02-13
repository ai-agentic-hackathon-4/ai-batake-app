import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { LucideIcon } from "lucide-react"

interface MetricCardProps {
    title: string
    value: string
    unit: string
    icon: LucideIcon
    status?: "normal" | "warning" | "critical"
}

export function MetricCard({ title, value, unit, icon: Icon, status = "normal" }: MetricCardProps) {
    const statusColors = {
        normal: "text-primary",
        warning: "text-chart-2",
        critical: "text-destructive",
    }

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
                <Icon className={`h-5 w-5 ${statusColors[status]}`} />
            </CardHeader>
            <CardContent>
                <div className="flex items-baseline gap-1">
                    <span className={`text-2xl sm:text-3xl lg:text-4xl font-bold ${statusColors[status]}`}>{value}</span>
                    <span className="text-lg text-muted-foreground">{unit}</span>
                </div>
            </CardContent>
        </Card>
    )
}
