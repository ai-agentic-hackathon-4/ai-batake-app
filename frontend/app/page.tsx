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
                        AI-powered smart farming platform for monitoring, research, and guidance.
                    </p>
                </div>

                {/* Features Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-200">

                    {/* Dashboard Card */}
                    <Link href="/dashboard" className="group">
                        <div className="h-full bg-white border border-slate-200 rounded-xl p-6 hover:shadow-lg hover:border-primary/50 transition-all duration-300">
                            <div className="mb-4 p-3 bg-blue-50 rounded-lg w-fit mx-auto group-hover:scale-110 transition-transform">
                                <Activity className="h-8 w-8 text-blue-600" />
                            </div>
                            <h2 className="text-xl font-semibold mb-2 text-slate-900">Dashboard</h2>
                            <p className="text-slate-500 text-sm">
                                Real-time monitoring of environmental data and plant growth status.
                            </p>
                        </div>
                    </Link>

                    {/* Research Agent Card */}
                    <Link href="/research_agent" className="group">
                        <div className="h-full bg-white border border-slate-200 rounded-xl p-6 hover:shadow-lg hover:border-primary/50 transition-all duration-300">
                            <div className="mb-4 p-3 bg-purple-50 rounded-lg w-fit mx-auto group-hover:scale-110 transition-transform">
                                <Microscope className="h-8 w-8 text-purple-600" />
                            </div>
                            <h2 className="text-xl font-semibold mb-2 text-slate-900">Research Agent</h2>
                            <p className="text-slate-500 text-sm">
                                AI-driven seed packet analysis and deep research for optimal growing conditions.
                            </p>
                        </div>
                    </Link>

                    {/* Seed Guide Card (Feature #5) */}
                    <Link href="/seed_guide" className="group">
                        <div className="h-full bg-white border border-slate-200 rounded-xl p-6 hover:shadow-lg hover:border-primary/50 transition-all duration-300">
                            <div className="mb-4 p-3 bg-green-50 rounded-lg w-fit mx-auto group-hover:scale-110 transition-transform">
                                <Sprout className="h-8 w-8 text-green-600" />
                            </div>
                            <h2 className="text-xl font-semibold mb-2 text-slate-900">Seed Guide (Async)</h2>
                            <p className="text-slate-500 text-sm">
                                Upload a photo to generate a step-by-step planting guide using async AI jobs.
                            </p>
                            <div className="mt-4 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                New Feature
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
                                AI-generated daily diary from sensor data and agent logs for tracking plant growth.
                            </p>
                            <div className="mt-4 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                                New Feature
                            </div>
                        </div>
                    </Link>

                </div>

                <footer className="text-sm text-slate-400 pt-8">
                    © 2025 Smart Farm AI Team
                </footer>
            </div>
        </div>
    )
}
