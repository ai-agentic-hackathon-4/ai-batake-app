import Link from "next/link"
import { Leaf, Sprout, Microscope, Activity, BookOpen, Sparkles } from "lucide-react"
import Image from "next/image"

export default function LandingPage() {
    return (
        <div className="h-screen bg-gradient-to-b from-green-50 to-white flex flex-col overflow-hidden">
            <div className="flex-1 flex flex-col items-center justify-center px-4 py-4 max-w-5xl w-full mx-auto">

                {/* Compact Hero */}
                <div className="flex flex-col items-center justify-center mb-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <div className="relative w-full max-w-5xl mx-auto aspect-[16/9] mb-4 [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_100%)]">
                        <Image
                            src="/saib-AI.png"
                            alt="Saib-AI"
                            fill
                            className="object-contain"
                            priority
                        />
                    </div>
                    <p className="text-lg md:text-2xl text-slate-600 font-bold max-w-xl mx-auto leading-relaxed opacity-90 text-center -mt-4 md:-mt-10 relative z-10">
                        育てる苦労はAIへ。<br className="md:hidden" />育つ喜びはあなたへ。
                    </p>
                </div>

                {/* Main CTA */}
                <Link href="/unified" className="group block w-full max-w-3xl mb-5 animate-in fade-in slide-in-from-bottom-6 duration-1000 delay-100">
                    <div className="relative overflow-hidden bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl px-6 py-5 text-white shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-0.5">
                        <div className="absolute top-0 right-0 p-2 opacity-10">
                            <Sparkles className="w-40 h-40 text-white" />
                        </div>
                        <div className="relative z-10 flex items-center gap-4">
                            <div className="p-3 bg-white/20 rounded-full backdrop-blur-sm group-hover:bg-white/30 transition-colors shrink-0">
                                <Sparkles className="w-8 h-8 text-white" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <h2 className="text-xl md:text-2xl font-bold">野菜を育て始める</h2>
                                <p className="text-green-50 text-sm mt-0.5">
                                    種袋の画像ひとつで、キャラクター・栽培ガイド・詳細リサーチを一括生成
                                </p>
                            </div>
                            <div className="bg-white text-green-600 px-5 py-1.5 rounded-full font-bold text-sm shadow-md group-hover:scale-105 transition-transform shrink-0">
                                スタート
                            </div>
                        </div>
                    </div>
                </Link>

                {/* Primary Features - 2 columns */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-3xl mb-4 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-200">
                    <Link href="/dashboard" className="group">
                        <div className="h-full bg-white border border-slate-200 rounded-xl p-5 hover:shadow-lg hover:border-blue-300 transition-all duration-300 flex items-center gap-4">
                            <div className="p-3 bg-blue-50 rounded-lg group-hover:scale-110 transition-transform shrink-0">
                                <Activity className="h-7 w-7 text-blue-600" />
                            </div>
                            <div>
                                <p className="font-semibold text-slate-900">ダッシュボード</p>
                                <p className="text-xs text-slate-400 mt-0.5">環境データと植物の成長状態をリアルタイムで監視</p>
                            </div>
                        </div>
                    </Link>

                    <Link href="/diary" className="group">
                        <div className="h-full bg-white border border-slate-200 rounded-xl p-5 hover:shadow-lg hover:border-amber-300 transition-all duration-300 flex items-center gap-4">
                            <div className="p-3 bg-amber-50 rounded-lg group-hover:scale-110 transition-transform shrink-0">
                                <BookOpen className="h-7 w-7 text-amber-600" />
                            </div>
                            <div>
                                <p className="font-semibold text-slate-900">育成日記</p>
                                <p className="text-xs text-slate-400 mt-0.5">日々の栽培記録とAIからのメッセージ</p>
                            </div>
                        </div>
                    </Link>
                </div>

                {/* Secondary Tools - subdued */}
                <div className="w-full max-w-3xl animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
                    <div className="flex items-center gap-3 justify-center mb-2">
                        <div className="h-px bg-slate-200 flex-1"></div>
                        <span className="text-[11px] text-slate-400 font-medium tracking-wide uppercase">ツール</span>
                        <div className="h-px bg-slate-200 flex-1"></div>
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                        <Link href="/character" className="group">
                            <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 text-center hover:bg-white hover:border-pink-200 hover:shadow-sm transition-all">
                                <Sparkles className="h-4 w-4 text-pink-400 mx-auto mb-1" />
                                <p className="text-xs font-medium text-slate-600">キャラクター</p>
                            </div>
                        </Link>
                        <Link href="/research_agent" className="group">
                            <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 text-center hover:bg-white hover:border-purple-200 hover:shadow-sm transition-all">
                                <Microscope className="h-4 w-4 text-purple-400 mx-auto mb-1" />
                                <p className="text-xs font-medium text-slate-600">リサーチ</p>
                            </div>
                        </Link>
                        <Link href="/seed_guide" className="group">
                            <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 text-center hover:bg-white hover:border-emerald-200 hover:shadow-sm transition-all">
                                <Sprout className="h-4 w-4 text-emerald-400 mx-auto mb-1" />
                                <p className="text-xs font-medium text-slate-600">栽培ガイド</p>
                            </div>
                        </Link>
                    </div>
                </div>

            </div>
        </div>
    )
}
