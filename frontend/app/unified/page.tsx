"use client"

import { useState, useRef, useEffect } from "react"
import { FileUp, Loader2, Sparkles, CheckCircle2, AlertCircle, Microscope, Sprout, Info, ChevronLeft, ChevronRight, Upload, Activity } from 'lucide-react';
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"

// Types
interface UnifiedJobStatus {
    job_id: string
    created_at: string
    image_url?: string
    research: { status: string; result?: any; error?: string }
    guide: { status: string; result?: any; steps?: any[]; error?: string }
    character: { status: string; result?: any; error?: string }
}

export default function UnifiedPage() {
    const [file, setFile] = useState<File | null>(null)
    const [preview, setPreview] = useState<string | null>(null)
    const [jobId, setJobId] = useState<string | null>(null)
    const [status, setStatus] = useState<UnifiedJobStatus | null>(null)
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string>('');
    const [currentStep, setCurrentStep] = useState(0); // For carousel navigation
    // Poll for status
    useEffect(() => {
        if (!jobId) return

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/unified/jobs/${jobId}`)
                if (!res.ok) throw new Error("Failed to fetch status")
                const data = await res.json()
                setStatus(data)

                // Stop polling if all completed or failed
                const isAllDone =
                    (data.research.status === "completed" || data.research.status === "failed") &&
                    (data.guide.status === "COMPLETED" || data.guide.status === "FAILED") &&
                    (data.character.status === "COMPLETED" || data.character.status === "FAILED")

                if (isAllDone) {
                    clearInterval(interval)
                }
            } catch (err) {
                console.error("Polling error:", err)
            }
        }, 3000)

        return () => clearInterval(interval)
    }, [jobId])

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const f = e.target.files[0]
            setFile(f)
            const reader = new FileReader()
            reader.onloadend = () => setPreview(reader.result as string)
            reader.readAsDataURL(f)
        }
    }

    const startAnalysis = async () => {
        if (!file) return
        setIsUploading(true)
        setError('')

        const formData = new FormData()
        formData.append("file", file)

        try {
            const res = await fetch("/api/unified/start", {
                method: "POST",
                body: formData,
            })

            if (!res.ok) throw new Error("Failed to start analysis")

            const data = await res.json()
            setJobId(data.job_id)
        } catch (err: any) {
            setError(err.message)
        } finally {
            setIsUploading(false)
        }
    }

    // Helper to determine step status color
    const getStatusColor = (s?: string) => {
        if (!s) return "text-slate-400"
        if (s.toLowerCase() === "pending" || s.toLowerCase() === "processing") return "text-blue-500 animate-pulse"
        if (s.toLowerCase() === "completed" || s.toLowerCase() === "success") return "text-green-500"
        if (s.toLowerCase() === "failed") return "text-red-500"
        return "text-slate-400" // Default
    }

    const getStatusIcon = (s?: string) => {
        if (!s) return <div className="h-5 w-5 rounded-full border-2 border-slate-200" />
        if (s.toLowerCase() === "pending" || s.toLowerCase() === "processing") return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
        if (s.toLowerCase() === "completed" || s.toLowerCase() === "success") return <CheckCircle2 className="h-5 w-5 text-green-500" />
        if (s.toLowerCase() === "failed") return <AlertCircle className="h-5 w-5 text-red-500" />
        return <div className="h-5 w-5 rounded-full border-2 border-slate-200" />
    }

    return (
        <div className="container mx-auto p-6 max-w-6xl">
            {/* Title Removed */}

            {/* Upload Section */}
            {!jobId && (
                <div className="min-h-[70vh] flex items-center justify-center">
                    <Card className="max-w-xl w-full border-dashed border-2">
                        <CardHeader>
                            <CardTitle className="text-center">種の袋をスキャン</CardTitle>
                            {/* Description Removed */}
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex flex-col items-center justify-center p-8 bg-slate-50 rounded-xl cursor-pointer hover:bg-slate-100 transition-colors border border-slate-200"
                                onClick={() => document.getElementById('file-upload')?.click()}>
                                {preview ? (
                                    <img src={preview} alt="Preview" className="max-h-64 rounded shadow-md" />
                                ) : (
                                    <div className="text-center space-y-2">
                                        <div className="bg-white p-4 rounded-full shadow-sm inline-block">
                                            <Upload className="h-8 w-8 text-primary" />
                                        </div>
                                        <p className="text-sm text-slate-500">クリックして画像をアップロード</p>
                                    </div>
                                )}
                                <input
                                    id="file-upload"
                                    type="file"
                                    className="hidden"
                                    accept="image/*"
                                    onChange={handleFileChange}
                                />
                            </div>

                            {error && (
                                <div className="p-3 bg-red-50 text-red-600 text-sm rounded flex items-center gap-2">
                                    <AlertCircle className="h-4 w-4" />
                                    {error}
                                </div>
                            )}

                            <Button
                                className="w-full h-12 text-lg"
                                disabled={!file || isUploading}
                                onClick={startAnalysis}
                            >
                                {isUploading ? (
                                    <>
                                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                        アップロード中...
                                    </>
                                ) : (
                                    <>
                                        <Sparkles className="mr-2 h-5 w-5" />
                                        解析を開始
                                    </>
                                )}
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Post-Upload Processing State */}
            {jobId && !status && (
                <div className="flex flex-col items-center justify-center py-24 space-y-6 animate-in fade-in zoom-in-95 duration-700">
                    <div className="relative">
                        <div className="absolute inset-0 bg-green-100 rounded-full animate-ping opacity-75"></div>
                        <div className="relative bg-white p-6 rounded-full shadow-xl border-4 border-green-50">
                            <Sprout className="h-16 w-16 text-green-600 animate-bounce" />
                        </div>
                    </div>
                    <div className="text-center space-y-2">
                        <h2 className="text-3xl font-bold text-slate-700">解析を開始しています...</h2>
                        <p className="text-slate-500 text-lg">種の袋から情報を読み取っています</p>
                    </div>
                </div>
            )}

            {/* Progress & Results Section */}
            {jobId && status && (
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

                    {/* Sidebar Status */}
                    <Card className="lg:col-span-1 h-fit">
                        <CardHeader>
                            <CardTitle className="text-lg">進行状況</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">

                            {/* CAHARCTER Status (First) */}
                            <div className="flex items-start gap-3">
                                <div className="mt-1">{getStatusIcon(status.character.status)}</div>
                                <div>
                                    <p className="font-medium flex items-center gap-2">
                                        <Sparkles className="h-4 w-4" /> キャラクター
                                    </p>
                                    <p className="text-xs text-slate-500 mt-1">
                                        {status.character.status === 'COMPLETED' ? '完了' :
                                            status.character.status === 'FAILED' ? '失敗' :
                                                status.character.status === 'PENDING' ? '待機中...' : (
                                                    <span className="flex items-center gap-1">
                                                        芽吹き中... <Loader2 className="h-4 w-4 animate-spin" />
                                                    </span>
                                                )}
                                    </p>
                                </div>
                            </div>

                            {/* RESEARCH Status (Second) */}
                            <div className="flex items-start gap-3">
                                <div className="mt-1">
                                    {(status.research.status === 'COMPLETED' || status.research.status === 'FAILED')
                                        ? getStatusIcon(status.research.status)
                                        : <Loader2 className="h-4 w-4 animate-spin text-purple-500" />}
                                </div>
                                <div>
                                    <p className="font-medium flex items-center gap-2">
                                        <Microscope className="h-4 w-4" /> 詳細リサーチ
                                    </p>
                                    <p className="text-xs text-slate-500 mt-1">
                                        {status.research.status === 'COMPLETED' ? '完了' :
                                            status.research.status === 'FAILED' ? '失敗' : '調査中...'}
                                    </p>
                                </div>
                            </div>

                            {/* GUIDE Status (Third) */}
                            <div className="flex items-start gap-3">
                                <div className="mt-1">{getStatusIcon(status.guide.status)}</div>
                                <div>
                                    <p className="font-medium flex items-center gap-2">
                                        <Sprout className="h-4 w-4" /> 栽培ガイド
                                    </p>
                                    <p className="text-xs text-slate-500 mt-1">
                                        {status.guide.status === 'COMPLETED' ? '完了' :
                                            status.guide.status === 'FAILED' ? '失敗' :
                                                status.guide.status === 'PENDING' ? '待機中...' : (
                                                    <span className="flex items-center gap-1">
                                                        生成中... <Loader2 className="h-4 w-4 animate-spin" />
                                                    </span>
                                                )}
                                    </p>
                                </div>
                            </div>

                        </CardContent>
                    </Card>

                    {/* Main Content Area */}
                    <div className="lg:col-span-3 space-y-8">

                        {/* 1. Immediate Seed Summary (Shows as soon as Research is done) */}
                        {status.research.result && (
                            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                                <Card className="bg-gradient-to-r from-emerald-50 to-green-50 border-emerald-100">
                                    <CardContent className="p-6 flex flex-col md:flex-row items-center justify-between gap-6">
                                        <div className="flex items-center gap-4">
                                            <div className="p-3 bg-white rounded-full shadow-sm">
                                                <Sprout className="h-8 w-8 text-green-600" />
                                            </div>
                                            <div>
                                                <h2 className="text-2xl font-bold text-slate-800">
                                                    {status.research.result.name}
                                                </h2>
                                            </div>
                                        </div>
                                        {/* Optional: Add quick action or status summary here */}
                                    </CardContent>
                                </Card>
                            </div>
                        )}

                        <Tabs defaultValue="summary" className="w-full">
                            <TabsList className="grid w-full grid-cols-3">
                                <TabsTrigger value="summary">キャラクター & 概要</TabsTrigger>
                                <TabsTrigger value="research">詳細リサーチ</TabsTrigger>
                                <TabsTrigger value="guide">栽培ガイド</TabsTrigger>
                            </TabsList>

                            {/* Summary Tab */}
                            <TabsContent value="summary" className="mt-6 space-y-8">

                                {/* Refined Character Display - Horizontal Layout */}
                                <div className="flex items-center justify-center">
                                    {status.character.result ? (
                                        <div className="w-full max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8 items-center animate-in fade-in duration-700">

                                            {/* Left: Character Image */}
                                            <div className="flex justify-center items-center">
                                                {status.character.result.image_url ? (
                                                    <div className="relative inline-block">
                                                        <div className="absolute inset-0 bg-yellow-100 rounded-full blur-2xl opacity-50 -z-10 transform scale-110"></div>
                                                        <img
                                                            src={status.character.result.image_url.startsWith('http') && !status.character.result.image_url.includes('/api/') ? status.character.result.image_url : `${status.character.result.image_url}`}
                                                            alt="Character"
                                                            className="w-full max-w-md mx-auto object-contain z-0 hover:scale-105 transition-transform duration-500 rounded-3xl border-8 border-white shadow-[0_0_0_8px_rgba(255,182,193,0.4)] bg-white"
                                                            style={{ maxHeight: '400px' }}
                                                        />
                                                    </div>
                                                ) : status.character.result.image_base64 ? (
                                                    <div className="relative inline-block">
                                                        <div className="absolute inset-0 bg-yellow-100 rounded-full blur-2xl opacity-50 -z-10 transform scale-110"></div>
                                                        <img
                                                            src={`data:image/png;base64,${status.character.result.image_base64}`}
                                                            alt="Character"
                                                            className="w-full max-w-md mx-auto object-contain z-0 rounded-3xl border-8 border-white shadow-[0_0_0_8px_rgba(255,182,193,0.4)] bg-white"
                                                            style={{ maxHeight: '400px' }}
                                                        />
                                                    </div>
                                                ) : (
                                                    <div className="w-64 h-64 bg-pink-50 rounded-full flex items-center justify-center mx-auto animate-pulse">
                                                        <Sparkles className="h-16 w-16 text-pink-200" />
                                                    </div>
                                                )}
                                            </div>

                                            {/* Right: Character Profile - Notebook Style */}
                                            <div className="space-y-6">
                                                {/* Profile Notebook Card */}
                                                <div className="relative bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 p-8 rounded-lg shadow-2xl border-4 border-amber-900/20"
                                                    style={{
                                                        backgroundImage: `repeating-linear-gradient(transparent, transparent 31px, #f59e0b15 31px, #f59e0b15 32px)`,
                                                        backgroundSize: '100% 32px'
                                                    }}>
                                                    {/* Notebook Binding Holes */}
                                                    <div className="absolute left-4 top-0 bottom-0 flex flex-col justify-around py-8">
                                                        <div className="w-3 h-3 rounded-full bg-slate-300 shadow-inner"></div>
                                                        <div className="w-3 h-3 rounded-full bg-slate-300 shadow-inner"></div>
                                                        <div className="w-3 h-3 rounded-full bg-slate-300 shadow-inner"></div>
                                                    </div>

                                                    {/* Red Margin Line */}
                                                    <div className="absolute left-12 top-0 bottom-0 w-0.5 bg-red-300/40"></div>

                                                    {/* Content */}
                                                    <div className="ml-8 space-y-4">
                                                        {/* Title Banner */}
                                                        <div className="relative inline-block">
                                                            <div className="absolute -top-2 -left-2 w-full h-full bg-pink-400/20 transform rotate-1 rounded"></div>
                                                            <h3 className="relative text-3xl font-bold text-pink-700 px-4 py-2 bg-white/60 rounded border-2 border-pink-300 shadow-sm"
                                                                style={{ fontFamily: '"Noto Sans JP", sans-serif' }}>
                                                                📝 {status.character.result.character_name || "名無しさん"}
                                                            </h3>
                                                        </div>

                                                        {/* Personality Section */}
                                                        <div className="bg-white/50 p-4 rounded-lg border-l-4 border-pink-400 shadow-sm">
                                                            <p className="text-sm text-pink-600 font-semibold mb-2">性格:</p>
                                                            <p className="text-slate-700 text-base leading-relaxed italic">
                                                                "{status.character.result.personality}"
                                                            </p>
                                                        </div>

                                                        {/* Catchphrase Sticker */}
                                                        <div className="flex justify-end">
                                                            <div className="relative">
                                                                <div className="absolute inset-0 bg-yellow-300 transform rotate-2 rounded-lg"></div>
                                                                <div className="relative bg-gradient-to-br from-yellow-200 to-yellow-300 px-5 py-3 rounded-lg shadow-lg border-2 border-yellow-400 transform -rotate-1">
                                                                    <p className="text-sm font-bold text-yellow-900 text-center">
                                                                        ✨ {status.character.result.catchphrase || "あなたの栽培パートナー"} ✨
                                                                    </p>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center p-12 text-slate-400 space-y-4">
                                            {status.character.status === 'FAILED' ? (
                                                <>
                                                    <AlertCircle className="h-12 w-12 text-red-300" />
                                                    <p>キャラクター召喚に失敗しました...</p>
                                                </>
                                            ) : (
                                                <>
                                                    <Loader2 className="h-12 w-12 animate-spin text-pink-300" />
                                                    <p className="text-lg">種から命が芽吹いています...</p>
                                                    <p className="text-sm">種の声を聞いています</p>
                                                </>
                                            )}
                                        </div>
                                    )}
                                </div>


                                {/* Basic Info Card */}
                                {status.research.result && (
                                    <div className="max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300">
                                        <Card className="bg-white/50 backdrop-blur border-emerald-100/50 shadow-sm">
                                            <CardHeader>
                                                <CardTitle className="flex items-center gap-2 text-emerald-700">
                                                    <Info className="h-5 w-5" /> 基本情報
                                                </CardTitle>
                                            </CardHeader>
                                            <CardContent className="space-y-4">
                                                <div className="p-4 bg-emerald-50/50 rounded-xl border border-emerald-100">
                                                    <p className="text-sm text-emerald-600 mb-1 font-medium">野菜の名前</p>
                                                    <p className="text-lg font-bold text-slate-800">{status.research.result.name}</p>
                                                </div>

                                                {/* Visible Instructions (if available) */}
                                                {status.research.result.basic_analysis?.visible_instructions && status.research.result.basic_analysis.visible_instructions !== "unknown" && (
                                                    <div className="md:col-span-3 p-4 bg-slate-50/50 rounded-xl border border-slate-100">
                                                        <p className="text-sm text-slate-600 mb-1 font-medium">📋 種袋の育て方ポイント</p>
                                                        <p className="text-base text-slate-800 whitespace-pre-wrap">{status.research.result.basic_analysis.visible_instructions}</p>
                                                    </div>
                                                )}
                                            </CardContent>
                                        </Card>
                                    </div>
                                )}

                            </TabsContent>

                            {/* Guide Tab */}
                            <TabsContent value="guide" className="mt-6">
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2 text-green-600">
                                            <Sprout className="h-5 w-5" /> ステップバイステップ・ガイド
                                        </CardTitle>
                                        <CardDescription>
                                            {status.guide.result?.description || "AIが作成した栽培プランです"}
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        {status.guide.status === 'COMPLETED' && status.guide.result && Array.isArray(status.guide.result) && status.guide.result.length > 0 ? (
                                            <div className="relative">
                                                {/* Carousel Container */}
                                                <div className="overflow-hidden">
                                                    <div
                                                        className="flex transition-transform duration-500 ease-in-out"
                                                        style={{ transform: `translateX(-${currentStep * 100}%)` }}
                                                    >
                                                        {status.guide.result.map((step: any, idx: number) => (
                                                            <div key={idx} className="flex-shrink-0 w-full p-4">
                                                                <div className="flex gap-4 border rounded-lg p-6 bg-gradient-to-br from-green-50 to-emerald-50">
                                                                    <div className="flex-shrink-0">
                                                                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 text-white flex items-center justify-center font-bold text-lg shadow-lg">
                                                                            {idx + 1}
                                                                        </div>
                                                                    </div>
                                                                    <div className="space-y-3 flex-1">
                                                                        <h3 className="font-bold text-xl text-green-700">{step.title}</h3>
                                                                        <p className="text-slate-700 leading-relaxed">{step.description}</p>
                                                                        {step.duration && (
                                                                            <span className="inline-block px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full font-medium">
                                                                                ⏱️ 目安: {step.duration}
                                                                            </span>
                                                                        )}
                                                                        {step.image_url && (
                                                                            <div className="mt-4">
                                                                                <img
                                                                                    src={step.image_url}
                                                                                    alt={step.title}
                                                                                    className="rounded-lg max-h-64 w-full object-cover border-2 border-green-200 shadow-md"
                                                                                />
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>

                                                {/* Navigation Controls */}
                                                <div className="flex items-center justify-between mt-6">
                                                    <button
                                                        onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                                                        disabled={currentStep === 0}
                                                        className="p-3 rounded-full bg-green-600 text-white disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-green-700 transition-colors shadow-lg"
                                                    >
                                                        <ChevronLeft className="h-6 w-6" />
                                                    </button>

                                                    <div className="text-center">
                                                        <p className="text-sm text-slate-600 font-medium">
                                                            ステップ {currentStep + 1} / {status.guide.result.length}
                                                        </p>
                                                    </div>

                                                    <button
                                                        onClick={() => setCurrentStep(Math.min(status.guide.result.length - 1, currentStep + 1))}
                                                        disabled={currentStep === status.guide.result.length - 1}
                                                        className="p-3 rounded-full bg-green-600 text-white disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-green-700 transition-colors shadow-lg"
                                                    >
                                                        <ChevronRight className="h-6 w-6" />
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="py-12 text-center text-slate-400 space-y-4">
                                                <Loader2 className="h-12 w-12 animate-spin mx-auto text-green-300" />
                                                <p className="text-lg">栽培ガイド執筆中...</p>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            </TabsContent>

                            {/* Research Tab */}
                            <TabsContent value="research" className="mt-6">
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2 text-purple-600">
                                            <Microscope className="h-5 w-5" /> 詳細リサーチデータ
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        {status.research.status?.toLowerCase() === 'completed' && status.research.result ? (
                                            <div className="space-y-6">
                                                {/* Name */}
                                                {status.research.result.name && (
                                                    <div className="bg-emerald-50 p-4 rounded-lg border border-emerald-200">
                                                        <h3 className="font-semibold text-emerald-800 mb-2 flex items-center gap-2">
                                                            <Sprout className="h-4 w-4" /> 野菜名
                                                        </h3>
                                                        <p className="text-slate-700">{status.research.result.name}</p>
                                                    </div>
                                                )}

                                                {/* Temperature */}
                                                {status.research.result.optimal_temp_range && (
                                                    <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                                                        <h3 className="font-semibold text-orange-800 mb-2 flex items-center gap-2">
                                                            <Activity className="h-4 w-4" /> 最適温度
                                                        </h3>
                                                        <p className="text-slate-700">{status.research.result.optimal_temp_range}</p>
                                                    </div>
                                                )}

                                                {/* Humidity */}
                                                {status.research.result.optimal_humidity_range && (
                                                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                                                        <h3 className="font-semibold text-blue-800 mb-2">💧 最適湿度</h3>
                                                        <p className="text-slate-700">{status.research.result.optimal_humidity_range}</p>
                                                    </div>
                                                )}

                                                {/* Soil Moisture */}
                                                {status.research.result.soil_moisture_standard && (
                                                    <div className="bg-amber-50 p-4 rounded-lg border border-amber-200">
                                                        <h3 className="font-semibold text-amber-800 mb-2">🌱 土壌水分量</h3>
                                                        <p className="text-slate-700">{status.research.result.soil_moisture_standard}</p>
                                                    </div>
                                                )}

                                                {/* Watering */}
                                                {status.research.result.watering_instructions && (
                                                    <div className="bg-cyan-50 p-4 rounded-lg border border-cyan-200">
                                                        <h3 className="font-semibold text-cyan-800 mb-2">💦 水やり方法</h3>
                                                        <p className="text-slate-700 whitespace-pre-wrap">{status.research.result.watering_instructions}</p>
                                                    </div>
                                                )}

                                                {/* Light Requirements */}
                                                {status.research.result.light_requirements && (
                                                    <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                                                        <h3 className="font-semibold text-yellow-800 mb-2">☀️ 日照条件</h3>
                                                        <p className="text-slate-700">{status.research.result.light_requirements}</p>
                                                    </div>
                                                )}

                                                {/* Care Tips */}
                                                {status.research.result.care_tips && (
                                                    <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                                                        <h3 className="font-semibold text-purple-800 mb-2">📝 栽培のコツ</h3>
                                                        <p className="text-slate-700 whitespace-pre-wrap">{status.research.result.care_tips}</p>
                                                    </div>
                                                )}

                                                {/* Summary Prompt */}
                                                {status.research.result.summary_prompt && (
                                                    <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                                                        <h3 className="font-semibold text-slate-800 mb-2">📋 詳細情報</h3>
                                                        <p className="text-slate-700 whitespace-pre-wrap leading-relaxed">{status.research.result.summary_prompt}</p>
                                                    </div>
                                                )}
                                            </div>
                                        ) : (
                                            <div className="py-12 flex flex-col items-center justify-center text-slate-400 space-y-4">
                                                {status.research.status?.toLowerCase() === 'failed' ? (
                                                    <div className="text-center space-y-4">
                                                        <AlertCircle className="h-16 w-16 text-red-400 mx-auto" />
                                                        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
                                                            <h3 className="text-lg font-bold text-red-800 mb-2">読み取りエラー</h3>
                                                            <p className="text-red-700 font-medium">
                                                                {status.research.error || "リサーチに失敗しました"}
                                                            </p>
                                                        </div>
                                                        <Button
                                                            onClick={() => {
                                                                setJobId(null);
                                                                setFile(null);
                                                                setPreview(null);
                                                                setStatus(null);
                                                            }}
                                                            variant="default"
                                                            className="bg-red-500 hover:bg-red-600 text-white"
                                                        >
                                                            <Upload className="mr-2 h-4 w-4" /> もう一度撮影・アップロードする
                                                        </Button>
                                                    </div>
                                                ) : (
                                                    <>
                                                        <Loader2 className="h-10 w-10 animate-spin text-purple-300" />
                                                        <p className="text-lg">詳細リサーチ実行中...</p>
                                                        <p className="text-sm">※完了まで少し時間がかかります</p>
                                                    </>
                                                )}
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            </TabsContent>

                        </Tabs>
                    </div>
                </div >
            )
            }
        </div >
    )
}
