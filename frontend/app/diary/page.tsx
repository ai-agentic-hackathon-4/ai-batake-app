"use client";

import { useEffect, useState } from "react";
import {
    Sprout,
    Calendar,
    TrendingUp,
    Lightbulb,
    ThermometerSun,
    Droplets,
    CloudRain,
    ChevronLeft,
    ChevronRight,
    RefreshCw,
    BookOpen,
} from "lucide-react";

interface DiaryStatistics {
    temperature: { min: number; max: number; avg: number };
    humidity: { min: number; max: number; avg: number };
    soil_moisture: { min: number; max: number; avg: number };
}

interface DiaryEvent {
    time: string;
    type: "action" | "warning" | "alert" | "info";
    device?: string;
    action: string;
}

interface GrowingDiary {
    id: string;
    date: string;
    vegetable_name?: string;
    statistics: DiaryStatistics;
    events: DiaryEvent[];
    ai_summary: string;
    observations: string;
    recommendations: string;
    plant_image_url?: string;
    generation_status: string;
    generation_time_ms?: number;
    agent_actions_count?: number;
}

export default function DiaryPage() {
    const [diaries, setDiaries] = useState<GrowingDiary[]>([]);
    const [selectedDiary, setSelectedDiary] = useState<GrowingDiary | null>(null);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);

    useEffect(() => {
        fetchDiaries();
    }, []);

    const fetchDiaries = async () => {
        setLoading(true);
        try {
            const res = await fetch("/api/diary/list?limit=30");
            if (res.ok) {
                const data = await res.json();
                setDiaries(data.diaries || []);
                // Auto-select the first diary
                if (data.diaries && data.diaries.length > 0 && !selectedDiary) {
                    setSelectedDiary(data.diaries[0]);
                }
            }
        } catch (error) {
            console.error("Failed to fetch diaries:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateToday = async () => {
        setGenerating(true);
        try {
            const today = new Date().toISOString().split("T")[0];
            const res = await fetch("/api/diary/generate-manual", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ date: today }),
            });

            if (res.ok) {
                alert("日記の生成を開始しました。数秒後に更新してください。");
                // Wait and refresh
                setTimeout(fetchDiaries, 5000);
            } else {
                alert("日記の生成に失敗しました。");
            }
        } catch (error) {
            console.error("Failed to generate diary:", error);
            alert("エラーが発生しました。");
        } finally {
            setGenerating(false);
        }
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString("ja-JP", {
            year: "numeric",
            month: "long",
            day: "numeric",
            weekday: "short",
        });
    };

    const getEventTypeColor = (type: string) => {
        switch (type) {
            case "alert":
                return "bg-red-500/10 text-red-500 border-red-500/20";
            case "warning":
                return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";
            case "action":
                return "bg-blue-500/10 text-blue-500 border-blue-500/20";
            default:
                return "bg-gray-500/10 text-gray-500 border-gray-500/20";
        }
    };

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b border-border bg-card">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-primary/10">
                                <BookOpen className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                                <h1 className="text-xl font-semibold text-card-foreground">
                                    育成日記
                                </h1>
                                <p className="text-sm text-muted-foreground">
                                    AI自動生成の栽培記録
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={handleGenerateToday}
                            disabled={generating}
                            className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2 gap-2"
                        >
                            {generating ? (
                                <RefreshCw className="w-4 h-4 animate-spin" />
                            ) : (
                                <Sprout className="w-4 h-4" />
                            )}
                            今日の日記を生成
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-8">
                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
                    </div>
                ) : diaries.length === 0 ? (
                    <div className="text-center py-16">
                        <Calendar className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
                        <h2 className="text-xl font-semibold mb-2">日記がありません</h2>
                        <p className="text-muted-foreground mb-6">
                            「今日の日記を生成」ボタンをクリックして最初の日記を作成しましょう。
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Diary List */}
                        <div className="lg:col-span-1 space-y-3">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Calendar className="w-5 h-5" />
                                日記一覧
                            </h2>
                            <div className="space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto pr-2">
                                {diaries.map((diary) => (
                                    <div
                                        key={diary.id}
                                        onClick={() => setSelectedDiary(diary)}
                                        className={`p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                                            selectedDiary?.id === diary.id
                                                ? "border-primary bg-primary/5"
                                                : "border-border bg-card hover:border-primary/50"
                                        }`}
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <span className="font-medium">
                                                {formatDate(diary.date)}
                                            </span>
                                            {diary.vegetable_name && (
                                                <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                                                    {diary.vegetable_name}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-sm text-muted-foreground line-clamp-2">
                                            {diary.ai_summary}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Diary Detail */}
                        <div className="lg:col-span-2">
                            {selectedDiary ? (
                                <div className="space-y-6">
                                    {/* Header */}
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <h2 className="text-2xl font-bold">
                                                {formatDate(selectedDiary.date)}
                                            </h2>
                                            {selectedDiary.vegetable_name && (
                                                <p className="text-muted-foreground flex items-center gap-2 mt-1">
                                                    <Sprout className="w-4 h-4" />
                                                    {selectedDiary.vegetable_name}の育成記録
                                                </p>
                                            )}
                                        </div>
                                    </div>

                                    {/* Statistics Cards */}
                                    <div className="grid grid-cols-3 gap-4">
                                        <div className="p-4 rounded-lg border border-border bg-card">
                                            <div className="flex items-center gap-2 text-orange-500 mb-2">
                                                <ThermometerSun className="w-5 h-5" />
                                                <span className="text-sm font-medium">気温</span>
                                            </div>
                                            <div className="text-2xl font-bold">
                                                {selectedDiary.statistics.temperature.avg}°C
                                            </div>
                                            <div className="text-xs text-muted-foreground mt-1">
                                                {selectedDiary.statistics.temperature.min}°C ~{" "}
                                                {selectedDiary.statistics.temperature.max}°C
                                            </div>
                                        </div>
                                        <div className="p-4 rounded-lg border border-border bg-card">
                                            <div className="flex items-center gap-2 text-blue-500 mb-2">
                                                <Droplets className="w-5 h-5" />
                                                <span className="text-sm font-medium">湿度</span>
                                            </div>
                                            <div className="text-2xl font-bold">
                                                {selectedDiary.statistics.humidity.avg}%
                                            </div>
                                            <div className="text-xs text-muted-foreground mt-1">
                                                {selectedDiary.statistics.humidity.min}% ~{" "}
                                                {selectedDiary.statistics.humidity.max}%
                                            </div>
                                        </div>
                                        <div className="p-4 rounded-lg border border-border bg-card">
                                            <div className="flex items-center gap-2 text-green-500 mb-2">
                                                <CloudRain className="w-5 h-5" />
                                                <span className="text-sm font-medium">土壌水分</span>
                                            </div>
                                            <div className="text-2xl font-bold">
                                                {selectedDiary.statistics.soil_moisture.avg}%
                                            </div>
                                            <div className="text-xs text-muted-foreground mt-1">
                                                {selectedDiary.statistics.soil_moisture.min}% ~{" "}
                                                {selectedDiary.statistics.soil_moisture.max}%
                                            </div>
                                        </div>
                                    </div>

                                    {/* AI Summary */}
                                    <div className="rounded-lg border border-border bg-card p-6">
                                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                            <Sprout className="w-5 h-5 text-primary" />
                                            今日の要約
                                        </h3>
                                        <p className="text-foreground leading-relaxed">
                                            {selectedDiary.ai_summary}
                                        </p>
                                    </div>

                                    {/* Observations & Recommendations */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="rounded-lg border border-border bg-card p-6">
                                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                                <TrendingUp className="w-5 h-5 text-blue-500" />
                                                成長観察
                                            </h3>
                                            <p className="text-muted-foreground leading-relaxed">
                                                {selectedDiary.observations}
                                            </p>
                                        </div>
                                        <div className="rounded-lg border border-border bg-card p-6">
                                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                                <Lightbulb className="w-5 h-5 text-yellow-500" />
                                                明日への提案
                                            </h3>
                                            <p className="text-muted-foreground leading-relaxed">
                                                {selectedDiary.recommendations}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Events Timeline */}
                                    {selectedDiary.events && selectedDiary.events.length > 0 && (
                                        <div className="rounded-lg border border-border bg-card p-6">
                                            <h3 className="text-lg font-semibold mb-4">
                                                主要イベント
                                            </h3>
                                            <div className="space-y-3">
                                                {selectedDiary.events.map((event, index) => (
                                                    <div
                                                        key={index}
                                                        className="flex items-start gap-3"
                                                    >
                                                        <span
                                                            className={`px-2 py-0.5 rounded text-xs font-medium border ${getEventTypeColor(
                                                                event.type
                                                            )}`}
                                                        >
                                                            {event.type}
                                                        </span>
                                                        <div className="flex-1">
                                                            <span className="text-sm">
                                                                {event.device && (
                                                                    <span className="font-medium mr-2">
                                                                        {event.device}:
                                                                    </span>
                                                                )}
                                                                {event.action}
                                                            </span>
                                                        </div>
                                                        <span className="text-xs text-muted-foreground">
                                                            {event.time
                                                                ? new Date(event.time).toLocaleTimeString(
                                                                      "ja-JP",
                                                                      {
                                                                          hour: "2-digit",
                                                                          minute: "2-digit",
                                                                      }
                                                                  )
                                                                : ""}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Generation Info */}
                                    {selectedDiary.generation_time_ms && (
                                        <div className="text-xs text-muted-foreground text-right">
                                            生成時間: {selectedDiary.generation_time_ms}ms |
                                            アクション数: {selectedDiary.agent_actions_count || 0}
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="flex items-center justify-center h-64 text-muted-foreground">
                                    日記を選択してください
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </main>

            {/* Footer */}
            <footer className="border-t border-border bg-card mt-auto">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <p className="text-sm text-muted-foreground text-center">
                        © 2025 Smart Farm AI - ハッカソンデモ
                    </p>
                </div>
            </footer>
        </div>
    );
}
