import Link from "next/link"
import { Leaf, Sprout, Microscope, Activity, BookOpen, Sparkles } from "lucide-react"

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

                <div className="w-full max-w-4xl mx-auto mb-12 animate-in fade-in slide-in-from-bottom-6 duration-1000 delay-100">
                    <Link href="/unified" className="group block">
                        <div className="relative overflow-hidden bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl p-8 text-white shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
                            <div className="absolute top-0 right-0 p-4 opacity-10">
                                <Sparkles className="w-64 h-64 text-white" />
                            </div>
                            <div className="relative z-10 flex flex-col md:flex-row items-center gap-6">
                                <div className="p-4 bg-white/20 rounded-full backdrop-blur-sm group-hover:bg-white/30 transition-colors">
                                    <Sparkles className="w-12 h-12 text-white" />
                                </div>
                                <div className="text-left flex-1">
                                    <h2 className="text-2xl md:text-3xl font-bold mb-2">野菜を育て始める</h2>
                                    <p className="text-green-50 text-lg">
                                        種袋の画像ひとつで、キャラクター・栽培ガイド・詳細リサーチを一括生成。
                                        あなたの農業ライフをここから始めましょう。
                                    </p>
                                </div>
                                <div className="bg-white text-green-600 px-6 py-2 rounded-full font-bold text-sm shadow-md group-hover:scale-105 transition-transform">
                                    スタート
                                </div>
                            </div>
                        </div>
                    </Link>
                </div>

                {/* Features Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-200">

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

                    {/* Growing Diary Card */}
                    <Link href="/diary" className="group">
                        <div className="h-full bg-white border border-slate-200 rounded-xl p-6 hover:shadow-lg hover:border-primary/50 transition-all duration-300">
                            <div className="mb-4 p-3 bg-amber-50 rounded-lg w-fit mx-auto group-hover:scale-110 transition-transform">
                                <BookOpen className="h-8 w-8 text-amber-600" />
                            </div>
                            <h2 className="text-xl font-semibold mb-2 text-slate-900">育成日記</h2>
                            <p className="text-slate-500 text-sm">
                                日々の栽培記録とAIからのメッセージを確認します。
                            </p>
                        </div>
                    </Link>
                </div>

                {/* Tools List */}
                <div className="w-full max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
                    <div className="bg-white border border-slate-200 rounded-2xl p-6 md:p-8 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 mb-4">ツール一覧</h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <Link href="/character" className="group">
                                <div className="h-full rounded-xl border border-slate-200 bg-slate-50 p-4 text-center hover:shadow-md hover:border-pink-300 transition-all">
                                    <div className="mx-auto mb-3 p-2 bg-pink-100 rounded-full w-fit">
                                        <Sparkles className="h-6 w-6 text-pink-600" />
                                    </div>
                                    <p className="font-semibold text-slate-900">キャラクター作成</p>
                                </div>
                            </Link>
                            <Link href="/research_agent" className="group">
                                <div className="h-full rounded-xl border border-slate-200 bg-slate-50 p-4 text-center hover:shadow-md hover:border-purple-300 transition-all">
                                    <div className="mx-auto mb-3 p-2 bg-purple-100 rounded-full w-fit">
                                        <Microscope className="h-6 w-6 text-purple-600" />
                                    </div>
                                    <p className="font-semibold text-slate-900">リサーチエージェント</p>
                                </div>
                            </Link>
                            <Link href="/seed_guide" className="group">
                                <div className="h-full rounded-xl border border-slate-200 bg-slate-50 p-4 text-center hover:shadow-md hover:border-emerald-300 transition-all">
                                    <div className="mx-auto mb-3 p-2 bg-emerald-100 rounded-full w-fit">
                                        <Sprout className="h-6 w-6 text-emerald-600" />
                                    </div>
                                    <p className="font-semibold text-slate-900">栽培ガイド作成</p>
                                </div>
                            </Link>
                        </div>
                    </div>
                </div>



                <footer className="text-sm text-slate-400 pt-8">
                    © 2025 Smart Farm AI チーム
                </footer>
            </div>
        </div>
    )
}
