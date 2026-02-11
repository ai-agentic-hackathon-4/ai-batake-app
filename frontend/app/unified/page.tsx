"use client"

import { useState, useRef, useEffect } from "react"
import { FileUp, Loader2, Sparkles, CheckCircle2, AlertCircle, Microscope, Sprout, Info, ChevronLeft, ChevronRight, Upload, Activity, Search, LayoutDashboard, UserPlus, ArrowLeft } from 'lucide-react';
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { GroundingDisplay } from "@/components/grounding-display";

// Types
interface UnifiedJobStatus {
    job_id: string
    created_at: string
    image_url?: string
    research: { status: string; id?: string; result?: any; error?: string }
    guide: { status: string; result?: any; steps?: any[]; error?: string }
    character: { status: string; id?: string; result?: any; error?: string }
}

const getProxiedImageUrl = (url?: string) => {
    if (!url) return "";
    if (url.startsWith("https://storage.googleapis.com/ai-agentic-hackathon-4-bk/seed-guides/output/")) {
        // Extract job_id and index from URL: .../output/{job_id}_{timestamp}_{index}.jpg
        const parts = url.split("/");
        const fileName = parts[parts.length - 1];
        const fileParts = fileName.split("_");
        if (fileParts.length >= 3) {
            const jobId = fileParts[0];
            const indexStr = fileParts[fileParts.length - 1].split(".")[0];
            return `/api/seed-guide/image/${jobId}/${indexStr}`;
        }
    }
    return url;
};

export default function UnifiedPage() {
    const [file, setFile] = useState<File | null>(null)
    const [preview, setPreview] = useState<string | null>(null)
    const [jobId, setJobId] = useState<string | null>(null)
    const [status, setStatus] = useState<UnifiedJobStatus | null>(null)
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string>('');
    const [currentStep, setCurrentStep] = useState(0); // For carousel navigation
    const [researchMode, setResearchMode] = useState<"agent" | "grounding">("grounding");
    const [imageModel, setImageModel] = useState<string>("pro");
    const [guideImageMode, setGuideImageMode] = useState<string>("single");
    const [showRawReport, setShowRawReport] = useState(false);
    const [isApplying, setIsApplying] = useState(false);
    const [isSelectingChar, setIsSelectingChar] = useState(false);
    const [charSelected, setCharSelected] = useState(false);

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
            const res = await fetch(`/api/unified/start?research_mode=${researchMode}&image_model=${imageModel}&guide_image_mode=${guideImageMode}`, {
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

    const handleApplyToAgent = async () => {
        if (!status?.research?.id) return;
        setIsApplying(true);
        try {
            const res = await fetch(`/api/vegetables/${status.research.id}/select`, {
                method: "POST",
            });
            if (res.ok) {
                alert("エージェントへの設定を更新しました。");
            } else {
                alert("設定の更新に失敗しました。");
            }
        } catch (e) {
            console.error(e);
            alert("エラーが発生しました。");
        } finally {
            setIsApplying(false);
        }
    };

    const handleSelectCharacterForDiary = async () => {
        if (!status?.character?.id) return;
        setIsSelectingChar(true);
        try {
            const res = await fetch(`/api/character/${status.character.id}/select`, {
                method: 'POST',
            });
            if (res.ok) {
                setCharSelected(true);
            } else {
                alert("キャラクターの登録に失敗しました。");
            }
        } catch (e) {
            console.error(e);
            alert("通信エラーが発生しました。");
        } finally {
            setIsSelectingChar(false);
        }
    };

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

    const isAllCompleted = status &&
        status.research.status.toLowerCase() === "completed" &&
        status.guide.status.toLowerCase() === "completed" &&
        status.character.status.toLowerCase() === "completed";

    return (
        <div className="min-h-screen bg-background flex flex-col">
            {/* Header */}
            <header className="border-b border-border bg-card">
                <div className="max-w-6xl mx-auto px-4 py-2.5 flex items-center gap-3">
                    <Link href="/" className="mr-2 p-1 hover:bg-accent rounded-full transition-colors">
                        <ArrowLeft className="h-5 w-5 text-muted-foreground" />
                    </Link>
                    <div className="p-1.5 sm:p-2 rounded-lg bg-primary/10">
                        <Sparkles className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                    </div>
                    <div className="min-w-0">
                        <h1 className="text-base sm:text-xl font-semibold text-card-foreground truncate">野菜を育て始める</h1>
                        <p className="text-xs sm:text-sm text-muted-foreground hidden sm:block">種袋スキャンで栽培ガイド・キャラクターを一括生成</p>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 w-full max-w-6xl mx-auto px-2 sm:px-4 py-2 sm:py-3 flex flex-col">

                {/* Upload Section */}
                {!jobId && (
                    <div className="flex-1 flex items-center justify-center py-8 w-full p-4">
                        <Card className="max-w-2xl w-full border-2 shadow-2xl rounded-2xl overflow-hidden border-slate-100">
                            <CardHeader className="pb-4 bg-slate-50/50 border-b border-slate-100">
                                <CardTitle className="text-center text-xl font-bold text-slate-800">種の袋をスキャン</CardTitle>
                                <CardDescription className="text-center text-xs">AIが情報を読み取り、栽培プランとキャラクターを生成します</CardDescription>
                            </CardHeader>
                            <CardContent className="p-6 space-y-6">
                                {/* Upload Box */}
                                <div className="flex flex-col items-center justify-center p-8 bg-slate-50 rounded-2xl cursor-pointer hover:bg-slate-100 transition-all border-2 border-dashed border-slate-200 hover:border-primary/50 group"
                                    onClick={() => document.getElementById('file-upload')?.click()}>
                                    {preview ? (
                                        <div className="relative">
                                            <img src={preview} alt="Preview" className="max-h-56 rounded-xl shadow-lg border-4 border-white" />
                                            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/10 rounded-xl">
                                                <p className="bg-white/90 px-3 py-1 rounded-full text-xs font-bold shadow-sm">変更する</p>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="text-center space-y-3">
                                            <div className="bg-white p-4 rounded-full shadow-md inline-block group-hover:scale-110 transition-transform">
                                                <Upload className="h-8 w-8 text-primary" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-bold text-slate-700">クリックして画像をアップロード</p>
                                            </div>
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

                                <div className="space-y-2 pb-1">
                                    <p className="text-xs font-medium text-slate-700">リサーチモードの選択</p>
                                    <Tabs value={researchMode} onValueChange={(val) => setResearchMode(val as any)} className="w-full">
                                        <TabsList className="grid w-full grid-cols-2">
                                            <TabsTrigger value="agent" className="text-xs">Deep Research</TabsTrigger>
                                            <TabsTrigger value="grounding" className="text-xs">Web Grounding</TabsTrigger>
                                        </TabsList>
                                    </Tabs>
                                    <p className="text-[10px] text-slate-400 text-center italic">
                                        {researchMode === "agent"
                                            ? "Deep Research: AIが時間をかけて徹底的に調査します (約20-30分)"
                                            : "Web Grounding: 最新のGoogle検索結果を元に素早く回答します (約1分)"}
                                    </p>
                                    {researchMode === "agent" && (
                                        <div className="flex items-start gap-2 p-2.5 bg-amber-50 border border-amber-200 rounded-lg">
                                            <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
                                            <p className="text-[11px] text-amber-700">⚠️ Deep Researchは処理が非常に重く、完了まで<strong>20〜30分</strong>かかる場合があります。Web Groundingの利用をおすすめします。</p>
                                        </div>
                                    )}
                                </div>

                                <div className="space-y-2 pb-1 pt-1 border-t border-slate-100">
                                    <p className="text-xs font-medium text-slate-700">🎨 図解モード</p>
                                    <div className="flex gap-2">
                                        <button
                                            type="button"
                                            onClick={() => setGuideImageMode("single")}
                                            className={`flex-1 text-xs px-3 py-2 rounded-lg border font-medium transition-all ${guideImageMode === "single"
                                                ? "bg-gradient-to-r from-green-500 to-emerald-600 text-white border-green-500 shadow-md"
                                                : "bg-white text-slate-600 border-slate-200 hover:border-green-300"
                                                }`}
                                        >
                                            🖼️ 1枚絵（Pro）
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setGuideImageMode("per_step")}
                                            className={`flex-1 text-xs px-3 py-2 rounded-lg border font-medium transition-all ${guideImageMode === "per_step"
                                                ? "bg-gradient-to-r from-green-500 to-emerald-600 text-white border-green-500 shadow-md"
                                                : "bg-white text-slate-600 border-slate-200 hover:border-green-300"
                                                }`}
                                        >
                                            📸 ステップ別
                                        </button>
                                    </div>
                                    {guideImageMode === "per_step" && (
                                        <div className="flex items-start gap-2 p-2.5 bg-amber-50 border border-amber-200 rounded-lg">
                                            <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
                                            <p className="text-[11px] text-amber-700">⚠️ ステップ別は各工程ごとに画像を生成するため、処理に<strong>かなり時間がかかります</strong>。通常は1枚絵（Pro）をおすすめします。</p>
                                        </div>
                                    )}
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* Research Mode */}
                                    <div className="space-y-3">
                                        <div className="flex items-center gap-2">
                                            <Search className="h-4 w-4 text-slate-400" />
                                            <p className="text-xs font-bold text-slate-700 uppercase tracking-wider">リサーチモード</p>
                                        </div>
                                        <Tabs value={researchMode} onValueChange={(val) => setResearchMode(val as any)} className="w-full">
                                            <TabsList className="grid w-full grid-cols-2 bg-slate-100 h-9 p-1">
                                                <TabsTrigger value="agent" className="text-[10px] sm:text-xs">Deep</TabsTrigger>
                                                <TabsTrigger value="grounding" className="text-[10px] sm:text-xs">Grounding</TabsTrigger>
                                            </TabsList>
                                        </Tabs>
                                        <p className="text-[10px] text-slate-500 leading-relaxed min-h-[32px]">
                                            {researchMode === "agent"
                                                ? "AIが時間をかけて徹底的に調査します (20-30分)"
                                                : "最新のGoogle検索結果を元に素早く回答します (1分)"}
                                        </p>
                                    </div>

                                    {/* Illustration Mode */}
                                    <div className="space-y-3">
                                        <div className="flex items-center gap-2">
                                            <Sparkles className="h-4 w-4 text-slate-400" />
                                            <p className="text-xs font-bold text-slate-700 uppercase tracking-wider">図解モード</p>
                                        </div>
                                        <div className="flex gap-2">
                                            <button
                                                type="button"
                                                onClick={() => setGuideImageMode("single")}
                                                className={`flex-1 text-[10px] sm:text-xs h-9 rounded-md border-2 font-bold transition-all ${guideImageMode === "single"
                                                    ? "bg-white text-primary border-primary shadow-sm"
                                                    : "bg-slate-50 text-slate-500 border-transparent hover:border-slate-200"
                                                    }`}
                                            >
                                                🖼️ 1枚絵
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setGuideImageMode("per_step")}
                                                className={`flex-1 text-[10px] sm:text-xs h-9 rounded-md border-2 font-bold transition-all ${guideImageMode === "per_step"
                                                    ? "bg-white text-primary border-primary shadow-sm"
                                                    : "bg-slate-50 text-slate-500 border-transparent hover:border-slate-200"
                                                    }`}
                                            >
                                                📸 ステップ
                                            </button>
                                        </div>
                                        <p className="text-[10px] text-slate-500 leading-relaxed min-h-[32px]">
                                            {guideImageMode === "single"
                                                ? "Proモデルによる高品質な1枚の俯瞰図を作成します"
                                                : "全工程ごとの挿絵を個別に生成します"}
                                        </p>
                                    </div>
                                </div>

                                {/* Message Area (Reserved Height to prevent shift) */}
                                <div className="space-y-4 min-h-[64px] flex flex-col justify-center">
                                    {/* Warning Banners */}
                                    {(researchMode === "agent" || guideImageMode === "per_step") && (
                                        <div className="p-3 bg-amber-50 border border-amber-100 rounded-xl flex items-start gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
                                            <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
                                            <p className="text-[10px] text-amber-700 leading-normal">
                                                <strong>注意:</strong> 現在の選択モードは処理に<strong>10分以上</strong>かかる場合があります。素早い結果を希望される場合は、Grounding / 1枚絵モードをお勧めします。
                                            </p>
                                        </div>
                                    )}

                                    {error && (
                                        <div className="p-3 bg-red-50 text-red-600 text-xs rounded-xl flex items-center gap-2 border border-red-100">
                                            <AlertCircle className="h-4 w-4" />
                                            {error}
                                        </div>
                                    )}
                                </div>

                                {/* Dashboard Link (Enabled only when all done) */}
                                <div className="pt-3 sm:pt-4 mt-3 sm:mt-0 border-t border-slate-100">
                                    <Button
                                        className="w-full h-12 text-base font-bold rounded-xl shadow-lg hover:shadow-xl transition-all active:scale-[0.98]"
                                        disabled={!file || isUploading}
                                        onClick={startAnalysis}
                                    >
                                        <span>ダッシュボードへ</span>
                                        <LayoutDashboard className="h-4 w-4" />
                                    </Button>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* Post-Upload Processing State */}
                {jobId && !status && (
                    <div className="flex-1 flex flex-col items-center justify-center py-12 space-y-4 animate-in fade-in zoom-in-95 duration-700">
                        <div className="relative">
                            <div className="absolute inset-0 bg-green-100 rounded-full animate-ping opacity-75"></div>
                            <div className="relative bg-white p-4 rounded-full shadow-xl border-4 border-green-50">
                                <Sprout className="h-10 w-10 text-green-600 animate-bounce" />
                            </div>
                        </div>
                        <div className="text-center space-y-1">
                            <h2 className="text-xl font-bold text-slate-700">解析を開始しています...</h2>
                            <p className="text-slate-500 text-sm">種の袋から情報を読み取っています</p>
                        </div>
                    </div>
                )}

                {/* Progress & Results Section */}
                {jobId && status && (
                    <div className="grid grid-cols-1 lg:grid-cols-4 gap-3 sm:gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500">

                        {/* Sidebar Status */}
                        <Card className="lg:col-span-1 h-fit">
                            <CardHeader className="pb-2 px-3 sm:px-6">
                                <CardTitle className="text-sm sm:text-base">進行状況</CardTitle>
                            </CardHeader>
                            <CardContent className="px-3 sm:px-6 pb-3 sm:pb-6">
                                {/* Mobile: horizontal, Desktop: vertical */}
                                <div className="flex flex-row lg:flex-col gap-3 sm:gap-4 overflow-x-auto lg:overflow-x-visible">

                                    {/* CAHARCTER Status (First) */}
                                    <div className="flex items-start gap-2 sm:gap-3 min-w-0">
                                        <div className="mt-1 shrink-0">{getStatusIcon(status.character.status)}</div>
                                        <div className="min-w-0">
                                            <p className="font-medium flex items-center gap-1 sm:gap-2 text-xs sm:text-sm">
                                                <Sparkles className="h-3 w-3 sm:h-4 sm:w-4 shrink-0" /> <span className="truncate">キャラクター</span>
                                            </p>
                                            <p className="text-[10px] sm:text-xs text-slate-500 mt-0.5">
                                                {status.character.status === 'COMPLETED' ? '完了' :
                                                    status.character.status === 'FAILED' ? '失敗' :
                                                        status.character.status === 'PENDING' ? '待機中...' : (
                                                            <span className="flex items-center gap-1">
                                                                芽吹き中... <Loader2 className="h-3 w-3 animate-spin" />
                                                            </span>
                                                        )}
                                            </p>
                                        </div>
                                    </div>

                                    {/* RESEARCH Status (Second) */}
                                    <div className="flex items-start gap-2 sm:gap-3 min-w-0">
                                        <div className="mt-1 shrink-0">
                                            {(status.research.status === 'COMPLETED' || status.research.status === 'FAILED')
                                                ? getStatusIcon(status.research.status)
                                                : <Loader2 className="h-4 w-4 animate-spin text-purple-500" />}
                                        </div>
                                        <div className="min-w-0">
                                            <p className="font-medium flex items-center gap-1 sm:gap-2 text-xs sm:text-sm">
                                                <Microscope className="h-3 w-3 sm:h-4 sm:w-4 shrink-0" /> <span className="truncate">リサーチ</span>
                                            </p>
                                            <p className="text-[10px] sm:text-xs text-slate-500 mt-0.5">
                                                {status.research.status === 'COMPLETED' ? '完了' :
                                                    status.research.status === 'FAILED' ? '失敗' : '調査中...'}
                                            </p>
                                        </div>
                                    </div>

                                    {/* GUIDE Status (Third) */}
                                    <div className="flex items-start gap-2 sm:gap-3 min-w-0">
                                        <div className="mt-1 shrink-0">{getStatusIcon(status.guide.status)}</div>
                                        <div className="min-w-0">
                                            <p className="font-medium flex items-center gap-1 sm:gap-2 text-xs sm:text-sm">
                                                <Sprout className="h-3 w-3 sm:h-4 sm:w-4 shrink-0" /> <span className="truncate">栽培ガイド</span>
                                            </p>
                                            <p className="text-[10px] sm:text-xs text-slate-500 mt-0.5">
                                                {status.guide.status === 'COMPLETED' ? '完了' :
                                                    status.guide.status === 'FAILED' ? '失敗' :
                                                        status.guide.status === 'PENDING' ? '待機中...' : '生成中...'}
                                            </p>
                                        </div>
                                        {/* Optional: Add quick action or status summary here */}
                                    </CardContent>
                                </Card>
                            </div>
                        )}

                            <Tabs defaultValue="summary" className="w-full">
                                <TabsList className="grid w-full grid-cols-3">
                                    <TabsTrigger value="summary" className="text-[11px] sm:text-sm px-1 sm:px-3">キャラクター</TabsTrigger>
                                    <TabsTrigger value="research" className="text-[11px] sm:text-sm px-1 sm:px-3">リサーチ</TabsTrigger>
                                    <TabsTrigger value="guide" className="text-[11px] sm:text-sm px-1 sm:px-3">栽培ガイド</TabsTrigger>
                                </TabsList>

                                {/* Summary Tab */}
                                <TabsContent value="summary" className="mt-3 space-y-4">

                                    {/* Refined Character Display - Horizontal Layout */}
                                    <div className="flex items-center justify-center">
                                        {status.character.result ? (
                                            <div className="w-full max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4 items-center animate-in fade-in duration-700">

                                                {/* Left: Character Image */}
                                                <div className="flex justify-center items-center">
                                                    {status.character.result.image_url ? (
                                                        <div className="relative inline-block w-full max-w-[200px] sm:max-w-md">
                                                            <div className="absolute inset-0 bg-yellow-100 rounded-full blur-2xl opacity-50 -z-10 transform scale-110"></div>
                                                            <img
                                                                src={status.character.result.image_url.startsWith('http') && !status.character.result.image_url.includes('/api/') ? status.character.result.image_url : `${status.character.result.image_url}`}
                                                                alt="Character"
                                                                className="w-full mx-auto object-contain z-0 hover:scale-105 transition-transform duration-500 rounded-xl sm:rounded-2xl border-2 sm:border-4 border-white shadow-[0_0_0_2px_rgba(255,182,193,0.4)] sm:shadow-[0_0_0_4px_rgba(255,182,193,0.4)] bg-white"
                                                                style={{ maxHeight: '200px' }}
                                                            />
                                                        </div>
                                                    ) : status.character.result.image_base64 ? (
                                                        <div className="relative inline-block w-full max-w-[200px] sm:max-w-md">
                                                            <div className="absolute inset-0 bg-yellow-100 rounded-full blur-2xl opacity-50 -z-10 transform scale-110"></div>
                                                            <img
                                                                src={`data:image/png;base64,${status.character.result.image_base64}`}
                                                                alt="Character"
                                                                className="w-full mx-auto object-contain z-0 rounded-xl sm:rounded-2xl border-2 sm:border-4 border-white shadow-[0_0_0_2px_rgba(255,182,193,0.4)] sm:shadow-[0_0_0_4px_rgba(255,182,193,0.4)] bg-white"
                                                                style={{ maxHeight: '200px' }}
                                                            />
                                                        </div>
                                                    ) : (
                                                        <div className="w-40 h-40 sm:w-64 sm:h-64 bg-emerald-50 rounded-full flex items-center justify-center mx-auto animate-pulse">
                                                            <Sparkles className="h-10 w-10 sm:h-16 sm:w-16 text-emerald-200" />
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Right: Character Profile - Notebook Style */}
                                                <div className="space-y-3">
                                                    {/* Profile Notebook Card */}
                                                    <div className="relative bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 p-3 sm:p-5 rounded-lg shadow-xl border-2 border-amber-900/20"
                                                        style={{
                                                            backgroundImage: `repeating-linear-gradient(transparent, transparent 31px, #f59e0b15 31px, #f59e0b15 32px)`,
                                                            backgroundSize: '100% 32px'
                                                        }}>
                                                        {/* Notebook Binding Holes - hidden on very small screens */}
                                                        <div className="absolute left-2 sm:left-4 top-0 bottom-0 hidden sm:flex flex-col justify-around py-8">
                                                            <div className="w-3 h-3 rounded-full bg-slate-300 shadow-inner"></div>
                                                            <div className="w-3 h-3 rounded-full bg-slate-300 shadow-inner"></div>
                                                            <div className="w-3 h-3 rounded-full bg-slate-300 shadow-inner"></div>
                                                        </div>

                                                        {/* Red Margin Line - hidden on very small screens */}
                                                        <div className="absolute left-12 top-0 bottom-0 w-0.5 bg-red-300/40 hidden sm:block"></div>

                                                        {/* Content */}
                                                        <div className="sm:ml-8 space-y-2 sm:space-y-3">
                                                            {/* Title Banner */}
                                                            <div className="relative inline-block">
                                                                <div className="absolute -top-1 -left-1 w-full h-full bg-emerald-400/20 transform rotate-1 rounded"></div>
                                                                <h3 className="relative text-base sm:text-xl font-bold text-emerald-800 px-2 sm:px-3 py-1 sm:py-1.5 bg-white/60 rounded border-2 border-emerald-300 shadow-sm"
                                                                    style={{ fontFamily: '"Noto Sans JP", sans-serif' }}>
                                                                    🌱 {status.character.result.character_name || "名無しさん"}
                                                                </h3>
                                                            </div>

                                                            {/* Personality Section */}
                                                            <div className="bg-white/50 p-3 rounded-lg border-l-4 border-emerald-500 shadow-sm">
                                                                <p className="text-xs text-emerald-700 font-semibold mb-1">性格:</p>
                                                                <p className="text-slate-700 text-sm leading-relaxed italic">
                                                                    "{status.character.result.personality}"
                                                                </p>
                                                            </div>

                                                            {/* Catchphrase Sticker */}
                                                            <div className="flex justify-end">
                                                                <div className="relative">
                                                                    <div className="absolute inset-0 bg-yellow-300 transform rotate-2 rounded-lg"></div>
                                                                    <div className="relative bg-gradient-to-br from-yellow-200 to-yellow-300 px-4 py-2 rounded-lg shadow-lg border-2 border-yellow-400 transform -rotate-1">
                                                                        <p className="text-xs sm:text-sm font-bold text-yellow-900 text-center">
                                                                            ✨ {status.character.result.catchphrase || "あなたの栽培パートナー"} ✨
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            {/* Select for Diary Button */}
                                                            {status.character.id && (
                                                                <div className="pt-3 border-t border-amber-200/50">
                                                                    <button
                                                                        onClick={handleSelectCharacterForDiary}
                                                                        disabled={isSelectingChar || charSelected}
                                                                        className={`w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg font-bold text-sm transition-all duration-300 shadow-md ${charSelected
                                                                            ? 'bg-green-100 text-green-700 border-2 border-green-300 cursor-default'
                                                                            : 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-700 hover:to-teal-700 hover:shadow-lg transform hover:-translate-y-0.5'
                                                                            }`}
                                                                    >
                                                                        {isSelectingChar ? (
                                                                            <><Loader2 className="h-4 w-4 animate-spin" /> 登録中...</>
                                                                        ) : charSelected ? (
                                                                            <><CheckCircle2 className="h-4 w-4" /> 日記のパートナーに登録しました！</>
                                                                        ) : (
                                                                            <><UserPlus className="h-4 w-4" /> この子を日記で使う</>
                                                                        )}
                                                                    </button>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>

                                            </div>
                                        ) : (
                                            <div className="flex flex-col items-center justify-center p-8 text-slate-400 space-y-3">
                                                {status.character.status === 'FAILED' ? (
                                                    <>
                                                        <AlertCircle className="h-10 w-10 text-red-300" />
                                                        <p>キャラクター召喚に失敗しました...</p>
                                                    </>
                                                ) : (
                                                    <>
                                                        <Loader2 className="h-10 w-10 animate-spin text-emerald-300" />
                                                        <p className="text-base">種から命が芽吹いています...</p>
                                                        <p className="text-xs">種の声を聞いています</p>
                                                    </>
                                                )}
                                            </div>
                                        )}
                                    </div>


                                    {/* Basic Info Card */}
                                    {status.research.result && (
                                        <div className="max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300">
                                            <Card className="bg-white/50 backdrop-blur border-emerald-100/50 shadow-sm">
                                                <CardHeader className="px-3 sm:px-6">
                                                    <CardTitle className="flex items-center gap-2 text-emerald-700 text-sm sm:text-base">
                                                        <Info className="h-4 w-4 sm:h-5 sm:w-5 shrink-0" /> 基本情報
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent className="space-y-3 sm:space-y-4 px-3 sm:px-6">
                                                    <div className="p-3 sm:p-4 bg-emerald-50/50 rounded-xl border border-emerald-100">
                                                        <p className="text-xs sm:text-sm text-emerald-600 mb-1 font-medium">野菜の名前</p>
                                                        <p className="text-base sm:text-lg font-bold text-slate-800">{status.research.result.name}</p>
                                                    </div>

                                                    {/* Visible Instructions (if available) */}
                                                    {status.research.result.basic_analysis?.visible_instructions && status.research.result.basic_analysis.visible_instructions !== "unknown" && (
                                                        <div className="p-3 sm:p-4 bg-slate-50/50 rounded-xl border border-slate-100">
                                                            <p className="text-xs sm:text-sm text-slate-600 mb-1 font-medium">📋 種袋の育て方ポイント</p>
                                                            <p className="text-sm sm:text-base text-slate-800 whitespace-pre-wrap">{status.research.result.basic_analysis.visible_instructions}</p>
                                                        </div>
                                                    )}
                                                </CardContent>
                                            </Card>
                                        </div>
                                    )}

                                </TabsContent>

                                {/* Guide Tab */}
                                <TabsContent value="guide" className="mt-3">
                                    <Card>
                                        <CardHeader className="pb-2">
                                            <CardTitle className="flex items-center gap-2 text-green-600 text-base">
                                                <Sprout className="h-4 w-4" /> ステップバイステップ・ガイド
                                            </CardTitle>
                                            <CardDescription className="text-xs">
                                                {status.guide.result?.description || "AIが作成した栽培プランです"}
                                            </CardDescription>
                                        </CardHeader>
                                        <CardContent>
                                            {status.guide.status === 'COMPLETED' && status.guide.result && Array.isArray(status.guide.result) && status.guide.result.length > 0 ? (
                                                <div className="relative">
                                                    {/* Single Guide Image (if only step 0 has image) */}
                                                    {(() => {
                                                        const stepsWithImages = status.guide.result.filter((s: any) => s.image_url);
                                                        const isSingleImageMode = stepsWithImages.length <= 1 && status.guide.result[0]?.image_url;
                                                        if (isSingleImageMode) {
                                                            return (
                                                                <div className="mb-6">
                                                                    <p className="text-sm text-slate-500 mb-2 text-center font-medium">🎨 NanoBanana Pro によるガイド画像</p>
                                                                    <img
                                                                        src={getProxiedImageUrl(status.guide.result[0].image_url)}
                                                                        alt="栽培ガイド"
                                                                        className="rounded-xl w-full object-contain border-2 border-green-200 shadow-lg bg-white"
                                                                    />
                                                                </div>
                                                            );
                                                        }
                                                        return null;
                                                    })()}

                                                    {/* Carousel Container */}
                                                    <div className="overflow-hidden">
                                                        <div
                                                            className="flex transition-transform duration-500 ease-in-out"
                                                            style={{ transform: `translateX(-${currentStep * 100}%)` }}
                                                        >
                                                            {status.guide.result.map((step: any, idx: number) => (
                                                                <div key={idx} className="flex-shrink-0 w-full p-2">
                                                                    <div className="flex gap-3 border rounded-lg p-4 bg-gradient-to-br from-green-50 to-emerald-50">
                                                                        <div className="flex-shrink-0">
                                                                            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 text-white flex items-center justify-center font-bold text-sm shadow-lg">
                                                                                {idx + 1}
                                                                            </div>
                                                                        </div>
                                                                        <div className="space-y-2 flex-1">
                                                                            <h3 className="font-bold text-base text-green-700">{step.title}</h3>
                                                                            <p className="text-slate-700 text-sm leading-relaxed">{step.description}</p>
                                                                            {step.duration && (
                                                                                <span className="inline-block px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full font-medium">
                                                                                    ⏱️ 目安: {step.duration}
                                                                                </span>
                                                                            )}
                                                                            {/* Per-step image (only in per_step mode, skip step 0 in single mode) */}
                                                                            {step.image_url && (() => {
                                                                                const stepsWithImages = status.guide.result.filter((s: any) => s.image_url);
                                                                                const isSingleImageMode = stepsWithImages.length <= 1;
                                                                                if (isSingleImageMode && idx === 0) return null; // Already shown above
                                                                                return (
                                                                                    <div className="mt-3">
                                                                                        <img
                                                                                            src={getProxiedImageUrl(step.image_url)}
                                                                                            alt={step.title}
                                                                                            className="rounded-lg max-h-48 sm:max-h-80 w-full object-contain border-2 border-green-200 shadow-md bg-white"
                                                                                        />
                                                                                    </div>
                                                                                );
                                                                            })()}
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>

                                                    {/* Navigation Controls */}
                                                    <div className="flex items-center justify-between mt-3">
                                                        <button
                                                            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                                                            disabled={currentStep === 0}
                                                            className="p-2 rounded-full bg-green-600 text-white disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-green-700 transition-colors shadow"
                                                        >
                                                            <ChevronLeft className="h-5 w-5" />
                                                        </button>

                                                        <div className="text-center">
                                                            <p className="text-xs text-slate-600 font-medium">
                                                                ステップ {currentStep + 1} / {status.guide.result.length}
                                                            </p>
                                                        </div>

                                                        <button
                                                            onClick={() => setCurrentStep(Math.min(status.guide.result.length - 1, currentStep + 1))}
                                                            disabled={currentStep === status.guide.result.length - 1}
                                                            className="p-2 rounded-full bg-green-600 text-white disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-green-700 transition-colors shadow"
                                                        >
                                                            <ChevronRight className="h-5 w-5" />
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="flex flex-col items-center justify-center p-8 text-slate-400 space-y-3">
                                                    {status.character.status === 'FAILED' ? (
                                                        <>
                                                            <AlertCircle className="h-10 w-10 text-red-300" />
                                                            <p>キャラクター召喚に失敗しました...</p>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Loader2 className="h-10 w-10 animate-spin text-emerald-300" />
                                                            <p className="text-base">種から命が芽吹いています...</p>
                                                            <p className="text-xs">種の声を聞いています</p>
                                                        </>
                                                    )}
                                                </div>
                                            )}
                                        </CardContent>
                                    </Card>
                                </TabsContent>

                                {/* Research Tab */}
                                <TabsContent value="research" className="mt-3">
                                    <Card>
                                        <CardHeader className="pb-2 px-3 sm:px-6">
                                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                                                <CardTitle className="flex items-center gap-2 text-purple-600 text-sm sm:text-base">
                                                    <Microscope className="h-4 w-4 sm:h-5 sm:w-5 shrink-0" /> リサーチデータ
                                                </CardTitle>
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    className="bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-200 text-xs sm:text-sm w-full sm:w-auto"
                                                    onClick={handleApplyToAgent}
                                                    disabled={isApplying || !status.research.id || status.research.status?.toLowerCase() !== 'completed'}
                                                >
                                                    {isApplying ? (
                                                        <Loader2 className="h-3.5 w-3.5 sm:h-4 sm:w-4 animate-spin mr-1.5" />
                                                    ) : (
                                                        <Sparkles className="h-3.5 w-3.5 sm:h-4 sm:w-4 mr-1.5" />
                                                    )}
                                                    エージェントに適応
                                                </Button>
                                            </div>
                                        </CardHeader>
                                        <CardContent className="px-3 sm:px-6">
                                            {status.research.status?.toLowerCase() === 'completed' && status.research.result ? (
                                                <div className="space-y-2 sm:space-y-3">
                                                    {/* Name */}
                                                    {status.research.result.name && (
                                                        <div className="bg-emerald-50 p-3 rounded-lg border border-emerald-200">
                                                            <h3 className="font-semibold text-emerald-800 mb-2 flex items-center gap-2">
                                                                <Sprout className="h-4 w-4" /> 野菜名
                                                            </h3>
                                                            <p className="text-slate-700">{status.research.result.name}</p>
                                                        </div>
                                                    )}

                                                    {/* Temperature */}
                                                    {status.research.result.optimal_temp_range && (
                                                        <div className="bg-orange-50 p-3 rounded-lg border border-orange-200">
                                                            <h3 className="font-semibold text-orange-800 mb-2 flex items-center gap-2">
                                                                <Activity className="h-4 w-4" /> 最適温度
                                                            </h3>
                                                            <p className="text-slate-700">{status.research.result.optimal_temp_range}</p>
                                                        </div>
                                                    )}

                                                    {/* Humidity */}
                                                    {status.research.result.optimal_humidity_range && (
                                                        <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                                                            <h3 className="font-semibold text-blue-800 mb-2">💧 最適湿度</h3>
                                                            <p className="text-slate-700">{status.research.result.optimal_humidity_range}</p>
                                                        </div>
                                                    )}

                                                    {/* Soil Moisture */}
                                                    {status.research.result.soil_moisture_standard && (
                                                        <div className="bg-amber-50 p-3 rounded-lg border border-amber-200">
                                                            <h3 className="font-semibold text-amber-800 mb-2">🌱 土壌水分量</h3>
                                                            <p className="text-slate-700">{status.research.result.soil_moisture_standard}</p>
                                                        </div>
                                                    )}

                                                    {/* Watering */}
                                                    {status.research.result.watering_instructions && (
                                                        <div className="bg-cyan-50 p-3 rounded-lg border border-cyan-200">
                                                            <h3 className="font-semibold text-cyan-800 mb-2">💦 水やり方法</h3>
                                                            <p className="text-slate-700 whitespace-pre-wrap">{status.research.result.watering_instructions}</p>
                                                        </div>
                                                    )}

                                                    {/* Light Requirements */}
                                                    {status.research.result.light_requirements && (
                                                        <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
                                                            <h3 className="font-semibold text-yellow-800 mb-2">☀️ 日照条件</h3>
                                                            <p className="text-slate-700">{status.research.result.light_requirements}</p>
                                                        </div>
                                                    )}

                                                    {/* Care Tips */}
                                                    {status.research.result.care_tips && (
                                                        <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                                                            <h3 className="font-semibold text-purple-800 mb-2">📝 栽培のコツ</h3>
                                                            <p className="text-slate-700 whitespace-pre-wrap">{status.research.result.care_tips}</p>
                                                        </div>
                                                    )}

                                                    {/* Summary Prompt */}
                                                    {status.research.result.summary_prompt && (
                                                        <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                                                            <h3 className="font-semibold text-slate-800 mb-2">📋 詳細情報</h3>
                                                            <p className="text-slate-700 whitespace-pre-wrap leading-relaxed">{status.research.result.summary_prompt}</p>
                                                        </div>
                                                    )}

                                                    {/* Grounding Attribution */}
                                                    {status.research.result.grounding_metadata && (
                                                        <GroundingDisplay metadata={status.research.result.grounding_metadata} />
                                                    )}

                                                    {/* Raw Report Display */}
                                                    {status.research.result.raw_report && (
                                                        <div className="mt-8 border-t border-slate-200 pt-6">
                                                            <button
                                                                onClick={() => setShowRawReport(!showRawReport)}
                                                                className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors w-full group"
                                                            >
                                                                <div className={`p-1 rounded bg-slate-100 group-hover:bg-slate-200 transition-colors ${showRawReport ? 'rotate-90' : ''}`}>
                                                                    <ChevronRight className="h-3.5 w-3.5 transition-transform" />
                                                                </div>
                                                                AIの調査レポート原文を表示
                                                            </button>

                                                            {showRawReport && (
                                                                <div className="mt-3 p-3 sm:p-5 bg-slate-900 rounded-xl overflow-x-auto border border-slate-800 shadow-inner animate-in fade-in slide-in-from-top-2 duration-300">
                                                                    <pre className="text-[10px] sm:text-xs text-slate-300 font-mono leading-relaxed whitespace-pre-wrap break-all sm:break-normal">
                                                                        {status.research.result.raw_report}
                                                                    </pre>
                                                                </div>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            ) : (
                                                <div className="py-8 flex flex-col items-center justify-center text-slate-400 space-y-3">
                                                    {status.research.status?.toLowerCase() === 'failed' ? (
                                                        <div className="text-center space-y-3">
                                                            <AlertCircle className="h-12 w-12 text-red-400 mx-auto" />
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
                                                </div>
                                            ) : (
                                            <div className="py-8 text-center text-slate-400 space-y-3">
                                                <Loader2 className="h-10 w-10 animate-spin mx-auto text-green-300" />
                                                <p className="text-base">栽培ガイド執筆中...</p>
                                            </div>
                                            )}
                                        </CardContent>
                                    </Card>
                                </TabsContent>

                                {/* Research Tab */}
                                <TabsContent value="research" className="mt-3">
                                    <Card>
                                        <CardHeader className="pb-2 px-3 sm:px-6">
                                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                                                <CardTitle className="flex items-center gap-2 text-purple-600 text-sm sm:text-base">
                                                    <Microscope className="h-4 w-4 sm:h-5 sm:w-5 shrink-0" /> リサーチデータ
                                                </CardTitle>
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    className="bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-200 text-xs sm:text-sm w-full sm:w-auto"
                                                    onClick={handleApplyToAgent}
                                                    disabled={isApplying || !status.research.id || status.research.status?.toLowerCase() !== 'completed'}
                                                >
                                                    {isApplying ? (
                                                        <Loader2 className="h-3.5 w-3.5 sm:h-4 sm:w-4 animate-spin mr-1.5" />
                                                    ) : (
                                                        <Sparkles className="h-3.5 w-3.5 sm:h-4 sm:w-4 mr-1.5" />
                                                    )}
                                                    エージェントに適応
                                                </Button>
                                            </div>
                                        </CardHeader>
                                        <CardContent className="px-3 sm:px-6">
                                            {status.research.status?.toLowerCase() === 'completed' && status.research.result ? (
                                                <div className="space-y-2 sm:space-y-3">
                                                    {/* Name */}
                                                    {status.research.result.name && (
                                                        <div className="bg-emerald-50 p-3 rounded-lg border border-emerald-200">
                                                            <h3 className="font-semibold text-emerald-800 mb-2 flex items-center gap-2">
                                                                <Sprout className="h-4 w-4" /> 野菜名
                                                            </h3>
                                                            <p className="text-slate-700">{status.research.result.name}</p>
                                                        </div>
                                                    )}

                                                    {/* Temperature */}
                                                    {status.research.result.optimal_temp_range && (
                                                        <div className="bg-orange-50 p-3 rounded-lg border border-orange-200">
                                                            <h3 className="font-semibold text-orange-800 mb-2 flex items-center gap-2">
                                                                <Activity className="h-4 w-4" /> 最適温度
                                                            </h3>
                                                            <p className="text-slate-700">{status.research.result.optimal_temp_range}</p>
                                                        </div>
                                                    )}

                                                    {/* Humidity */}
                                                    {status.research.result.optimal_humidity_range && (
                                                        <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                                                            <h3 className="font-semibold text-blue-800 mb-2">💧 最適湿度</h3>
                                                            <p className="text-slate-700">{status.research.result.optimal_humidity_range}</p>
                                                        </div>
                                                    )}

                                                    {/* Soil Moisture */}
                                                    {status.research.result.soil_moisture_standard && (
                                                        <div className="bg-amber-50 p-3 rounded-lg border border-amber-200">
                                                            <h3 className="font-semibold text-amber-800 mb-2">🌱 土壌水分量</h3>
                                                            <p className="text-slate-700">{status.research.result.soil_moisture_standard}</p>
                                                        </div>
                                                    )}

                                                    {/* Watering */}
                                                    {status.research.result.watering_instructions && (
                                                        <div className="bg-cyan-50 p-3 rounded-lg border border-cyan-200">
                                                            <h3 className="font-semibold text-cyan-800 mb-2">💦 水やり方法</h3>
                                                            <p className="text-slate-700 whitespace-pre-wrap">{status.research.result.watering_instructions}</p>
                                                        </div>
                                                    )}

                                                    {/* Light Requirements */}
                                                    {status.research.result.light_requirements && (
                                                        <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
                                                            <h3 className="font-semibold text-yellow-800 mb-2">☀️ 日照条件</h3>
                                                            <p className="text-slate-700">{status.research.result.light_requirements}</p>
                                                        </div>
                                                    )}

                                                    {/* Care Tips */}
                                                    {status.research.result.care_tips && (
                                                        <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                                                            <h3 className="font-semibold text-purple-800 mb-2">📝 栽培のコツ</h3>
                                                            <p className="text-slate-700 whitespace-pre-wrap">{status.research.result.care_tips}</p>
                                                        </div>
                                                    )}

                                                    {/* Summary Prompt */}
                                                    {status.research.result.summary_prompt && (
                                                        <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                                                            <h3 className="font-semibold text-slate-800 mb-2">📋 詳細情報</h3>
                                                            <p className="text-slate-700 whitespace-pre-wrap leading-relaxed">{status.research.result.summary_prompt}</p>
                                                        </div>
                                                    )}

                                                    {/* Grounding Attribution */}
                                                    {status.research.result.grounding_metadata && (
                                                        <GroundingDisplay metadata={status.research.result.grounding_metadata} />
                                                    )}

                                                    {/* Raw Report Display */}
                                                    {status.research.result.raw_report && (
                                                        <div className="mt-8 border-t border-slate-200 pt-6">
                                                            <button
                                                                onClick={() => setShowRawReport(!showRawReport)}
                                                                className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors w-full group"
                                                            >
                                                                <div className={`p-1 rounded bg-slate-100 group-hover:bg-slate-200 transition-colors ${showRawReport ? 'rotate-90' : ''}`}>
                                                                    <ChevronRight className="h-3.5 w-3.5 transition-transform" />
                                                                </div>
                                                                AIの調査レポート原文を表示
                                                            </button>

                                                            {showRawReport && (
                                                                <div className="mt-3 p-3 sm:p-5 bg-slate-900 rounded-xl overflow-x-auto border border-slate-800 shadow-inner animate-in fade-in slide-in-from-top-2 duration-300">
                                                                    <pre className="text-[10px] sm:text-xs text-slate-300 font-mono leading-relaxed whitespace-pre-wrap break-all sm:break-normal">
                                                                        {status.research.result.raw_report}
                                                                    </pre>
                                                                </div>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            ) : (
                                                <div className="py-8 flex flex-col items-center justify-center text-slate-400 space-y-3">
                                                    {status.research.status?.toLowerCase() === 'failed' ? (
                                                        <div className="text-center space-y-3">
                                                            <AlertCircle className="h-12 w-12 text-red-400 mx-auto" />
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
                                                            <Loader2 className="h-12 w-12 animate-spin text-purple-300" />
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
            </main >
        </div >
    )
}
