import Link from "next/link"
import { Leaf, LayoutDashboard, FlaskConical, ArrowRight } from "lucide-react"

export default function Home() {
    return (
        <div className="min-h-screen bg-background">
            {/* Header (Same as Dashboard) */}
            <header className="border-b border-border bg-card">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-primary/10">
                            <Leaf className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold text-card-foreground">Smart Farm Portal</h1>
                            <p className="text-sm text-muted-foreground">AI栽培管理システムへようこそ</p>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-6 py-12 space-y-8">
                <div className="text-center space-y-4">
                    <h2 className="text-3xl font-bold tracking-tight">Select a Dashboard</h2>
                    <p className="text-muted-foreground max-w-2xl mx-auto">
                        アクセスしたいダッシュボードを選択してください。
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
                    {/* Main Dashboard Link */}
                    <Link href="/dashboard" className="group relative overflow-hidden rounded-xl border border-border bg-card p-6 transition-all hover:shadow-lg hover:border-accent/50">
                        <div className="flex items-start justify-between">
                            <div className="p-3 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                                <LayoutDashboard className="h-8 w-8 text-primary" />
                            </div>
                            <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                        </div>
                        <div className="mt-4 space-y-2">
                            <h3 className="text-xl font-semibold">Main Dashboard</h3>
                            <p className="text-sm text-muted-foreground">
                                現在の環境データ、カメラ画像、AIログを確認できます。
                            </p>
                        </div>
                    </Link>

                    {/* Research Agent Link */}
                    <Link href="/research_agent" className="group relative overflow-hidden rounded-xl border border-border bg-card p-6 transition-all hover:shadow-lg hover:border-accent/50">
                        <div className="flex items-start justify-between">
                            <div className="p-3 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                                <FlaskConical className="h-8 w-8 text-primary" />
                            </div>
                            <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                        </div>
                        <div className="mt-4 space-y-2">
                            <h3 className="text-xl font-semibold">Research Agent</h3>
                            <p className="text-sm text-muted-foreground">
                                新しい種の登録、Deep Researchのステータス管理を行えます。
                            </p>
                        </div>
                    </Link>
                </div>
            </main>

            {/* Footer */}
            <footer className="border-t border-border bg-card mt-auto fixed bottom-0 w-full">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <p className="text-sm text-muted-foreground text-center">© 2025 Smart Farm AI</p>
                </div>
            </footer>
        </div>
    )
}
