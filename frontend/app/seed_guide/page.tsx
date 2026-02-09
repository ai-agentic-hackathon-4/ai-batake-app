"use client"

import React, { useState, useEffect } from 'react';
import { Upload, ArrowLeft, ArrowRight, Sprout, AlertCircle, Loader2, BookOpen, Clock, CheckCircle, XCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import Link from 'next/link';

interface Step {
    title: string;
    description: string;
    image_base64: string | null;
    image_url?: string;
    error?: string;
}

interface SavedGuide {
    id: string;
    title: string;
    description?: string;
    status?: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
    message?: string;
    created_at: string;
    steps: Step[];
}

export default function SeedGuidePage() {
    // View State: 'create' | 'list' | 'detail'
    // Default to 'list' for the unified dashboard view
    const [viewMode, setViewMode] = useState<'create' | 'list' | 'detail'>('list');

    // Create Mode State
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);

    // List/Detail Mode State
    const [savedGuides, setSavedGuides] = useState<SavedGuide[]>([]);
    const [selectedGuide, setSelectedGuide] = useState<SavedGuide | null>(null);
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [isLoadingDetails, setIsLoadingDetails] = useState(false);

    // Auto-refresh interval for list
    useEffect(() => {
        fetchSavedGuides();
        const interval = setInterval(fetchSavedGuides, 5000); // 5 sec background refresh
        return () => clearInterval(interval);
    }, []);

    // Also poll specifically when viewing a processing guide
    useEffect(() => {
        let detailInterval: number;
        if (viewMode === 'detail' && selectedGuide && (selectedGuide.status === 'PENDING' || selectedGuide.status === 'PROCESSING') && !isLoadingDetails) {
            detailInterval = window.setInterval(async () => {
                try {
                    const res = await fetch(`/api/seed-guide/saved/${selectedGuide.id}`);
                    if (res.ok) {
                        const updated = await res.json();
                        setSelectedGuide(updated);
                        // Also update list cache
                        setSavedGuides(prev => prev.map(g => g.id === updated.id ? updated : g));
                    }
                } catch (e) { console.error(e); }
            }, 3000);
        }
        return () => clearInterval(detailInterval);
    }, [viewMode, selectedGuide, isLoadingDetails]);

    const fetchSavedGuides = async () => {
        try {
            const res = await fetch('/api/seed-guide/saved');
            if (res.ok) {
                const data = await res.json();
                setSavedGuides(data);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            const file = event.target.files[0];
            setSelectedFile(file);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        setError(null);

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            // Updated endpoint name
            const response = await fetch('/api/seed-guide/generate', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Upload failed");
            }

            // Successfully started
            await fetchSavedGuides();
            setViewMode('list'); // Switch to list to see progress
            setSelectedFile(null);

        } catch (err: any) {
            console.error(err);
            setError(err.message || "Failed to start generation.");
        }
    };

    const handleSelectGuide = async (guide: SavedGuide) => {
        // Optimistically set guide from list to get IDs etc
        setSelectedGuide(guide);
        setCurrentStepIndex(0);
        setViewMode('detail');
        setIsLoadingDetails(true);

        // Fetch full details (including hydrated images)
        try {
            const res = await fetch(`/api/seed-guide/saved/${guide.id}`);
            if (res.ok) {
                const fullGuide = await res.json();
                setSelectedGuide(fullGuide);
            }
        } catch (e) {
            console.error("Failed to fetch guide details:", e);
        } finally {
            setIsLoadingDetails(false);
        }
    };

    const handleDeleteGuide = async (id: string) => {
        if (!confirm("この栽培ガイドを削除しますか？")) return;
        try {
            const res = await fetch(`/api/seed-guide/saved/${id}`, { method: "DELETE" });
            if (!res.ok) throw new Error("Delete failed");
            if (selectedGuide?.id === id) {
                setSelectedGuide(null);
                setViewMode('list');
            }
            fetchSavedGuides();
        } catch (e) {
            console.error(e);
            setError("削除に失敗しました");
        }
    };

    const handleNext = () => {
        if (!selectedGuide) return;
        if (currentStepIndex < (selectedGuide.steps?.length || 0) - 1) {
            setCurrentStepIndex(prev => prev + 1);
        }
    };

    const handlePrev = () => {
        if (currentStepIndex > 0) {
            setCurrentStepIndex(prev => prev - 1);
        }
    };

    const getStatusBadge = (status?: string) => {
        switch (status) {
            case 'COMPLETED':
                return <Badge className="bg-green-500 hover:bg-green-600"><CheckCircle className="w-3 h-3 mr-1" /> 完了</Badge>;
            case 'PROCESSING':
            case 'PENDING':
                return <Badge className="bg-blue-500 hover:bg-blue-600"><Loader2 className="w-3 h-3 mr-1 animate-spin" /> 解析中</Badge>;
            case 'FAILED':
                return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" /> 失敗</Badge>;
            default:
                return <Badge variant="secondary">不明</Badge>;
        }
    };

    return (
        <div className="min-h-screen bg-background flex flex-col">
            {/* Header */}
            <header className="border-b border-border bg-card sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Link href="/" className="mr-2 p-1 hover:bg-accent rounded-full transition-colors">
                            <ArrowLeft className="h-5 w-5 text-muted-foreground" />
                        </Link>
                        <div className="p-2 rounded-lg bg-primary/10">
                            <Sprout className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold text-card-foreground">栽培ガイド生成</h1>
                            <p className="text-sm text-muted-foreground">AI栽培アシスタント</p>
                        </div>
                    </div>

                    {viewMode === 'list' && (
                        <button
                            onClick={() => setViewMode('create')}
                            className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
                        >
                            + ガイドを新規作成
                        </button>
                    )}
                    {(viewMode === 'create' || viewMode === 'detail') && (
                        <button
                            onClick={() => setViewMode('list')}
                            className="text-sm font-medium text-primary hover:underline flex items-center gap-2"
                        >
                            <BookOpen className="h-4 w-4" />
                            ガイド一覧
                        </button>
                    )}
                </div>
            </header>

            <main className="flex-1 max-w-7xl mx-auto px-6 py-8 w-full">

                {/* --- LIST VIEW --- */}
                {viewMode === 'list' && (
                    <div className="max-w-4xl mx-auto space-y-6">
                        <div className="flex justify-between items-center">
                            <h2 className="text-2xl font-bold">作成済みのガイド</h2>
                        </div>

                        {savedGuides.length === 0 ? (
                            <div className="text-center py-12 text-muted-foreground bg-card rounded-lg border border-dashed border-border">
                                <Sprout className="h-12 w-12 mx-auto mb-4 opacity-20" />
                                <p className="text-lg font-medium">ガイドがまだありません</p>
                                <p className="mb-4">種袋をアップロードして栽培ガイドを作成しましょう。</p>
                                <button
                                    onClick={() => setViewMode('create')}
                                    className="text-primary hover:underline"
                                >
                                    最初のガイドを作成する
                                </button>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {savedGuides.map((guide) => (
                                    <Card key={guide.id} className="hover:shadow-md transition-shadow cursor-pointer border-border" onClick={() => handleSelectGuide(guide)}>
                                        <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
                                            <CardTitle className="text-lg truncate pr-2">{guide.title || "無題のガイド"}</CardTitle>
                                            <div className="shrink-0 flex items-center gap-3">
                                                {getStatusBadge(guide.status)}
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDeleteGuide(guide.id);
                                                    }}
                                                    className="text-xs text-red-500 hover:text-red-600"
                                                >
                                                    削除
                                                </button>
                                            </div>
                                        </CardHeader>
                                        <CardContent>
                                            <p className="text-sm text-muted-foreground mb-4 line-clamp-2 h-10">
                                                {guide.status === 'PROCESSING' || guide.status === 'PENDING'
                                                    ? guide.message || "解析中..."
                                                    : guide.description || guide.steps?.[0]?.description || "説明なし"}
                                            </p>
                                            <div className="flex items-center text-xs text-muted-foreground gap-1">
                                                <Clock className="h-3 w-3" />
                                                {new Date(guide.created_at).toLocaleString()}
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* --- CREATE VIEW --- */}
                {viewMode === 'create' && (
                    <div className="max-w-2xl mx-auto">
                        <div className="text-center mb-8">
                            <h2 className="text-3xl font-bold mb-2">新しい栽培ガイドの生成</h2>
                            <p className="text-muted-foreground">種袋の写真をアップロードすると、AIが最適な栽培手順を画像付きで提案します。</p>
                        </div>

                        <Card>
                            <CardContent className="pt-8 flex flex-col items-center text-center space-y-6">
                                <div className="p-6 rounded-full bg-primary/5 mb-2">
                                    <Upload className="h-10 w-10 text-primary" />
                                </div>

                                <div className="w-full max-w-sm space-y-4">
                                    <div className="grid w-full items-center gap-1.5">
                                        <input
                                            type="file"
                                            accept="image/*"
                                            className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                                            onChange={handleFileChange}
                                        />
                                    </div>
                                    <button
                                        onClick={handleUpload}
                                        disabled={!selectedFile}
                                        className="inline-flex w-full items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-4 py-2"
                                    >
                                        {isLoadingDetails ? (
                                            <>
                                                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                                解析中...
                                            </>
                                        ) : (
                                            'アップロードして解析を開始'
                                        )}
                                    </button>
                                </div>

                                {error && (
                                    <div className="flex items-center gap-2 text-destructive bg-destructive/10 p-4 rounded-lg w-full text-left">
                                        <AlertCircle className="h-5 w-5 shrink-0" />
                                        <p className="text-sm">{error}</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* --- DETAIL VIEW --- */}
                {viewMode === 'detail' && selectedGuide && (
                    <div className="max-w-3xl mx-auto space-y-6">
                        {isLoadingDetails ? (
                            // Full Page Loading State
                            <div className="space-y-6 animate-pulse">
                                <div className="h-6 w-32 bg-muted rounded"></div>
                                <Card className="overflow-hidden border-border shadow-sm">
                                    <div className="aspect-video bg-muted relative flex items-center justify-center border-b border-border">
                                        <Loader2 className="h-12 w-12 text-muted-foreground animate-spin" />
                                    </div>
                                    <CardContent className="pt-6 space-y-4">
                                        <div className="h-8 w-3/4 bg-muted rounded"></div>
                                        <div className="h-px w-full bg-border" />
                                        <div className="space-y-2">
                                            <div className="h-4 w-full bg-muted rounded"></div>
                                            <div className="h-4 w-full bg-muted rounded"></div>
                                            <div className="h-4 w-5/6 bg-muted rounded"></div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        ) : (
                            <>
                                {/* Status Banner for Processing Items */}
                                {(selectedGuide.status === 'PENDING' || selectedGuide.status === 'PROCESSING') && (
                                    <Card className="border-blue-200 bg-blue-50 dark:bg-blue-900/20">
                                        <CardContent className="py-6 flex flex-col items-center text-center gap-2">
                                            <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
                                            <h3 className="font-semibold text-lg">AIによる解析を実行中...</h3>
                                            <p className="text-muted-foreground">{selectedGuide.message}</p>
                                            <p className="text-xs text-muted-foreground mt-2">このページを離れても大丈夫です。ガイドは自動的に保存されます。</p>
                                        </CardContent>
                                    </Card>
                                )}

                                {selectedGuide.status === 'FAILED' && (
                                    <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
                                        <CardContent className="py-6 flex flex-col items-center text-center gap-2">
                                            <XCircle className="h-8 w-8 text-destructive" />
                                            <h3 className="font-semibold text-lg">解析に失敗しました</h3>
                                            <p className="text-muted-foreground">{selectedGuide.message}</p>
                                        </CardContent>
                                    </Card>
                                )}

                                {/* Completed Steps View */}
                                {selectedGuide.status === 'COMPLETED' && selectedGuide.steps && selectedGuide.steps.length > 0 && (
                                    <div className="space-y-6">
                                        <div className="flex justify-between items-center text-sm text-muted-foreground">
                                            <span className="text-sm font-medium text-primary">ステップ {currentStepIndex + 1} / {selectedGuide.steps.length}</span>
                                            <div className="flex gap-1">
                                                {selectedGuide.steps.map((_, idx) => (
                                                    <div
                                                        key={idx}
                                                        className={`h-1.5 w-8 rounded-full transition-colors ${idx <= currentStepIndex ? 'bg-primary' : 'bg-muted'}`}
                                                    />
                                                ))}
                                            </div>
                                        </div>

                                        <Card className="overflow-hidden border-border shadow-sm">
                                            <div className="aspect-video bg-muted relative flex items-center justify-center border-b border-border">
                                                {(() => {
                                                    const step = selectedGuide.steps[currentStepIndex];
                                                    const imageUrl = step.image_url;
                                                    const imageBase64 = step.image_base64;

                                                    if (imageBase64) {
                                                        return (
                                                            <img
                                                                src={`data:image/jpeg;base64,${imageBase64}`}
                                                                alt={step.title}
                                                                className="w-full h-full object-cover animate-in fade-in duration-500"
                                                            />
                                                        );
                                                    } else if (imageUrl) {
                                                        // Should rely on parent loading state, but safe fallback
                                                        return (
                                                            <div className="flex flex-col items-center justify-center h-full w-full bg-muted/50 text-muted-foreground animate-pulse">
                                                                <Loader2 className="h-10 w-10 mb-3 animate-spin text-primary/50" />
                                                                <span className="text-sm font-medium">画像を読み込み中...</span>
                                                            </div>
                                                        );
                                                    } else {
                                                        return (
                                                            <div className="flex flex-col items-center text-muted-foreground">
                                                                <Sprout className="h-12 w-12 mb-2 opacity-20" />
                                                                <span>画像がありません</span>
                                                            </div>
                                                        );
                                                    }
                                                })()}
                                            </div>
                                            <CardContent className="pt-6 space-y-4">
                                                <h3 className="text-2xl font-bold tracking-tight">{selectedGuide.steps[currentStepIndex].title}</h3>
                                                <div className="h-px w-full bg-border" />
                                                <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">手順の詳細</h4>
                                                <p className="text-lg leading-relaxed text-muted-foreground">
                                                    {selectedGuide.steps[currentStepIndex].description}
                                                </p>
                                            </CardContent>
                                        </Card>

                                        <div className="flex justify-between pt-4">
                                            <button
                                                onClick={handlePrev}
                                                disabled={currentStepIndex === 0}
                                                className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2 gap-2"
                                            >
                                                <ArrowLeft className="h-4 w-4" /> 戻る
                                            </button>

                                            <div className="flex gap-3">
                                                <button
                                                    onClick={() => handleDeleteGuide(selectedGuide.id)}
                                                    className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-red-200 text-red-600 bg-white shadow-sm hover:bg-red-50 h-10 px-4 py-2"
                                                >
                                                    削除
                                                </button>
                                                <button
                                                    onClick={() => setViewMode('list')}
                                                    className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2 gap-2"
                                                >
                                                    一覧に戻る
                                                </button>
                                                <button
                                                    onClick={handleNext}
                                                    disabled={currentStepIndex === (selectedGuide.steps.length) - 1}
                                                    className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-4 py-2 gap-2"
                                                >
                                                    次へ <ArrowRight className="h-4 w-4" />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
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
