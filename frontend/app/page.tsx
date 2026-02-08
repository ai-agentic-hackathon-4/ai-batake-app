import Link from "next/link"
import { Leaf, Sprout, Microscope, Activity, BookOpen } from "lucide-react"

export default function LandingPage() {
    return (
        <div className="min-h-screen bg-gradient-to-b from-green-50 to-white flex flex-col items-center justify-center p-4">
            <div className="max-w-4xl w-full space-y-12 text-center">

                {/* Hero Section */}
                <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <div className="mx-auto p-4 bg-primary/10 rounded-full w-fit">
                        <Leaf className="h-12 w-12 text-primary" />
                    </div>
                    <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-slate-900">
                        AI Batake App
                    </h1>
                    <p className="text-xl text-slate-600 max-w-2xl mx-auto">
                        AIを活用したスマート農業プラットフォーム。監視、研究、そして栽培ガイドを提供します。
                    </p>
                </div>

                {/* Features Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 w-full animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-200">

                    {/* Dashboard Card */}
                    <Link href="/dashboard" className="group">
                        <div className="h-full bg-white border border-slate-200 rounded-xl p-6 hover:shadow-lg hover:border-primary/50 transition-all duration-300">
                            <div className="mb-4 p-3 bg-blue-50 rounded-lg w-fit mx-auto group-hover:scale-110 transition-transform">
                                <Activity className="h-8 w-8 text-blue-600" />
                            </div>
                            <h2 className="text-xl font-semibold mb-2 text-slate-900">ダッシュボード</h2>
                            <p className="text-slate-500 text-sm">
                                環境データと植物の成長状態をリアルタイムで監視します。
                            </p>
                        </div>
                    </Link>

                    {/* Research Agent Card */}
                    <Link href="/research_agent" className="group">
                        <div className="h-full bg-white border border-slate-200 rounded-xl p-6 hover:shadow-lg hover:border-primary/50 transition-all duration-300">
                            <div className="mb-4 p-3 bg-purple-50 rounded-lg w-fit mx-auto group-hover:scale-110 transition-transform">
                                <Microscope className="h-8 w-8 text-purple-600" />
                            </div>
                            <h2 className="text-xl font-semibold mb-2 text-slate-900">リサーチエージェント</h2>
                            <p className="text-slate-500 text-sm">
                                AIによる種袋分析と、最適な栽培条件の詳細調査を行います。
                            </p>
                        </div>
                    </Link>

                    {/* Seed Guide Card (Feature #5) */}
                    <Link href="/seed_guide" className="group">
                        <div className="h-full bg-white border border-slate-200 rounded-xl p-6 hover:shadow-lg hover:border-primary/50 transition-all duration-300">
                            <div className="mb-4 p-3 bg-green-50 rounded-lg w-fit mx-auto group-hover:scale-110 transition-transform">
                                <Sprout className="h-8 w-8 text-green-600" />
                            </div>
                            <h2 className="text-xl font-semibold mb-2 text-slate-900">栽培ガイド生成</h2>
                            <p className="text-slate-500 text-sm">
                                写真をアップロードして、AIがステップバイステップの栽培ガイドを作成します。
                            </p>
                            <div className="mt-4 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                新機能
                            </div>
                        </div>
                    </Link>

                    {/* Growing Diary Card */}
                    <Link href="/diary" className="group">
                        <div className="h-full bg-white border border-slate-200 rounded-xl p-6 hover:shadow-lg hover:border-primary/50 transition-all duration-300">
                            <div className="mb-4 p-3 bg-amber-50 rounded-lg w-fit mx-auto group-hover:scale-110 transition-transform">
                                <BookOpen className="h-8 w-8 text-amber-600" />
                            </div>
                            <h2 className="text-xl font-semibold mb-2 text-slate-900">育成日記</h2>
                            <p className="text-slate-500 text-sm">
                                センサーデータやログからAIが生成する日々の栽培記録を確認します。
                            </p>
                            <div className="mt-4 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                                新機能
                            </div>
                        </div>
                    </Link>

                </div>

                <footer className="text-sm text-slate-400 pt-8">
                    © 2025 Smart Farm AI チーム
                </footer>
            </div>
        </div>
    )
}
