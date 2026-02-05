"use client"

import { Sprout } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useEffect, useState } from "react"

// GrowthStage enum mapping (from backend)
enum GrowthStage {
    SPROUT = 1,      // 発芽 (Sprout)
    SEEDLING = 2,    // 育苗 (Seedling)
    VEGETATIVE = 3,  // 栄養成長 (Vegetative)
    FLOWERING = 4,   // 開花・結実 (Flowering/Fruiting)
    HARVEST = 5      // 収穫 (Harvest)
}

// Stage name mapping
const stageNames: Record<GrowthStage, string> = {
    [GrowthStage.SPROUT]: "発芽期",
    [GrowthStage.SEEDLING]: "育苗期",
    [GrowthStage.VEGETATIVE]: "栄養成長期",
    [GrowthStage.FLOWERING]: "開花・結実期",
    [GrowthStage.HARVEST]: "収穫期",
}

interface AgentLog {
    id: string
    data?: {
        growth_stage?: number
    }
    timestamp: string
}

interface AgentLogsResponse {
    logs: AgentLog[]
}

export function GrowthStageCard() {
    const [currentGrowthStage, setCurrentGrowthStage] = useState<GrowthStage>(GrowthStage.SPROUT)
    const [daysSincePlanting, setDaysSincePlanting] = useState<number>(0)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        const fetchGrowthStage = async () => {
            try {
                const response = await fetch("http://localhost:8081/api/agent-logs")
                const data: AgentLogsResponse = await response.json()

                // Get the most recent log with growth_stage
                const latestLog = data.logs.find(log => log.data?.growth_stage)
                if (latestLog?.data?.growth_stage) {
                    setCurrentGrowthStage(latestLog.data.growth_stage as GrowthStage)
                }
            } catch (error) {
                console.error("Failed to fetch growth stage:", error)
            } finally {
                setIsLoading(false)
            }
        }

        const fetchDaysSincePlanting = async () => {
            try {
                const response = await fetch("http://localhost:8081/api/agent-logs/oldest")
                const data: { timestamp: string | null } = await response.json()

                if (data.timestamp) {
                    const plantingDate = new Date(data.timestamp).getTime()
                    const now = new Date().getTime()
                    const daysDiff = Math.floor((now - plantingDate) / (1000 * 60 * 60 * 24))
                    setDaysSincePlanting(daysDiff)
                }
            } catch (error) {
                console.error("Failed to fetch planting date:", error)
            }
        }

        fetchGrowthStage()
        fetchDaysSincePlanting()

        // Poll every 30 seconds
        const interval = setInterval(() => {
            fetchGrowthStage()
            fetchDaysSincePlanting()
        }, 30000)

        return () => clearInterval(interval)
    }, [])

    // Build stages array based on current growth stage
    const stages = [
        {
            name: stageNames[GrowthStage.SPROUT],
            completed: currentGrowthStage > GrowthStage.SPROUT,
            current: currentGrowthStage === GrowthStage.SPROUT
        },
        {
            name: stageNames[GrowthStage.SEEDLING],
            completed: currentGrowthStage > GrowthStage.SEEDLING,
            current: currentGrowthStage === GrowthStage.SEEDLING
        },
        {
            name: stageNames[GrowthStage.VEGETATIVE],
            completed: currentGrowthStage > GrowthStage.VEGETATIVE,
            current: currentGrowthStage === GrowthStage.VEGETATIVE
        },
        {
            name: stageNames[GrowthStage.FLOWERING],
            completed: currentGrowthStage > GrowthStage.FLOWERING,
            current: currentGrowthStage === GrowthStage.FLOWERING
        },
        {
            name: stageNames[GrowthStage.HARVEST],
            completed: false,
            current: currentGrowthStage === GrowthStage.HARVEST
        },
    ]

    const currentStage = stages.find((s) => s.current)
    const progress = ((currentGrowthStage - 1) / (Object.keys(GrowthStage).length / 2 - 1)) * 100

    if (isLoading) {
        return (
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-base font-medium flex items-center gap-2">
                        <Sprout className="h-5 w-5 text-primary" />
                        生育段階
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl bg-primary/10 animate-pulse">
                            <Sprout className="h-8 w-8 text-primary" />
                        </div>
                        <div className="space-y-2">
                            <div className="h-8 w-32 bg-muted rounded animate-pulse" />
                            <div className="h-4 w-24 bg-muted rounded animate-pulse" />
                        </div>
                    </div>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card>
            <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                    <Sprout className="h-5 w-5 text-primary" />
                    生育段階
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Current Stage Display */}
                <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-primary/10">
                        <Sprout className="h-8 w-8 text-primary" />
                    </div>
                    <div>
                        <p className="text-2xl font-semibold text-card-foreground">{currentStage?.name}</p>
                        <p className="text-sm text-muted-foreground">種まき開始から{daysSincePlanting}日目</p>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">進捗</span>
                        <span className="font-medium text-primary">{Math.round(progress)}%</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${progress}%` }} />
                    </div>
                </div>

                {/* Stage Timeline */}
                <div className="flex justify-between pt-2 border-t border-border">
                    {stages.map((stage, index) => (
                        <div key={stage.name} className="flex flex-col items-center gap-1">
                            <div
                                className={`w-3 h-3 rounded-full ${stage.current
                                    ? "bg-primary ring-2 ring-primary/30"
                                    : stage.completed
                                        ? "bg-primary"
                                        : "bg-muted-foreground/30"
                                    }`}
                            />
                            <span className={`text-xs ${stage.current ? "text-primary font-medium" : "text-muted-foreground"}`}>
                                {stage.name.slice(0, 2)}
                            </span>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}
