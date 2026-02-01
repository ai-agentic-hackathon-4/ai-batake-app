import { Sprout } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const stages = [
    { name: "発芽期", completed: true },
    { name: "栄養成長期", completed: true },
    { name: "開花期", current: true },
    { name: "結実期", completed: false },
    { name: "収穫期", completed: false },
]

export function GrowthStageCard() {
    const currentStage = stages.find((s) => s.current)
    const progress = (stages.filter((s) => s.completed).length / stages.length) * 100

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
                        <p className="text-sm text-muted-foreground">播種から42日目</p>
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
