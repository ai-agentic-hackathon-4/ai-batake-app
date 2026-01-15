import { Camera } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function PlantCamera() {
    return (
        <Card className="overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg font-medium flex items-center gap-2">
                    <Camera className="h-5 w-5 text-primary" />
                    プラントカメラ
                </CardTitle>
                <Badge variant="secondary" className="bg-primary/10 text-primary">
                    ライブ
                </Badge>
            </CardHeader>
            <CardContent className="p-0">
                <div className="relative aspect-video">
                    <img src="/healthy-green-tomato-plant-in-smart-greenhouse-wit.jpg" alt="植物のライブカメラ映像" className="w-full h-full object-cover" />
                    <div className="absolute bottom-3 left-3 bg-card/90 backdrop-blur-sm rounded-md px-3 py-1.5 text-sm">
                        最終更新: 2025/01/15 14:32
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
