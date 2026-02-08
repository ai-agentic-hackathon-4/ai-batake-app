"use client";

import { useEffect, useState, useRef } from "react";
import { Search, Plus, CloudUpload, Leaf, Clock, ArrowRight, ExternalLink, ArrowLeft, X, FlaskConical } from "lucide-react"
import Link from "next/link"
    ;

interface Vegetable {
    id: string;
    name: string;
    status: "processing" | "completed" | "failed";
    created_at: string;
    instructions?: Record<string, any>;
}

export default function ResearchDashboard() {
    const [vegetables, setVegetables] = useState<Vegetable[]>([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedVeg, setSelectedVeg] = useState<Vegetable | null>(null);
    const [uploading, setUploading] = useState(false);
    const [fileName, setFileName] = useState("Click to browse or drag file here");
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Poll for data
    useEffect(() => {
        fetchVegetables();
        const interval = setInterval(fetchVegetables, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchVegetables = async () => {
        try {
            const res = await fetch("/api/vegetables");
            if (res.ok) {
                const data = await res.json();
                setVegetables(data);
            }
        } catch (error) {
            console.error("Failed to fetch vegetables:", error);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFileName(e.target.files[0].name);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!fileInputRef.current?.files?.[0]) return;

        setUploading(true);
        const formData = new FormData();
        formData.append("file", fileInputRef.current.files[0]);

        try {
            const res = await fetch("/api/register-seed", {
                method: "POST",
                body: formData,
            });

            if (res.ok) {
                closeModal();
                fetchVegetables(); // Refresh immediately
            } else {
                alert("Upload failed");
            }
        } catch (error) {
            console.error(error);
            alert("Error uploading file");
        } finally {
            setUploading(false);
        }
    };

    const openModal = () => {
        setIsModalOpen(true);
        setFileName("Click to browse or drag file here");
        if (fileInputRef.current) fileInputRef.current.value = "";
    }

    const closeModal = () => setIsModalOpen(false);
    const closeDetailModal = () => setSelectedVeg(null);

    const isSystemExecuting = vegetables.some((v) => v.status === "processing");

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b border-border bg-card">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-3">
                            <Link href="/" className="mr-2 p-1 hover:bg-accent rounded-full transition-colors">
                                <ArrowLeft className="h-5 w-5 text-muted-foreground" />
                            </Link>
                            <div className="p-2 rounded-lg bg-primary/10">
                                <Leaf className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                                <h1 className="text-xl font-semibold text-card-foreground">リサーチエージェント</h1>
                                <p className="text-sm text-muted-foreground">AIによる栽培情報の深層調査</p>
                            </div>
                        </div>
                        <div className={`px-4 py-1.5 rounded-full text-sm font-medium flex items-center gap-2 border ${isSystemExecuting
                            ? "bg-blue-500/10 text-blue-500 border-blue-500/20"
                            : "bg-primary/10 text-primary border-primary/20"
                            }`}>
                            <div className={`w-2 h-2 rounded-full ${isSystemExecuting ? "bg-blue-500 animate-pulse" : "bg-primary"}`}></div>
                            {isSystemExecuting ? "深層調査を実行中..." : "システム待機中"}
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-8">
                <div className="flex justify-between items-center mb-8">
                    <h2 className="text-2xl font-semibold tracking-tight">野菜の研究情報</h2>
                    <button
                        onClick={openModal}
                        className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2 gap-2"
                    >
                        <Plus className="w-4 h-4" />
                        新しい種を登録
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {vegetables.map((veg) => {
                        const isProcessing = veg.status === "processing";
                        const isFailed = veg.status === "failed";
                        const isCompleted = veg.status === "completed";

                        return (
                            <div
                                key={veg.id}
                                className={`group relative rounded-xl border border-border bg-card p-6 shadow-sm transition-all hover:shadow-md cursor-pointer ${!isProcessing ? "hover:border-primary/50" : ""
                                    }`}
                                onClick={() => !isProcessing && setSelectedVeg(veg)}
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <h3 className="font-semibold text-lg leading-none tracking-tight">{veg.name}</h3>
                                        <p className="text-sm text-muted-foreground mt-1">ID: {veg.id.substring(0, 8)}...</p>
                                    </div>
                                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide border ${isProcessing
                                        ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
                                        : isFailed
                                            ? "bg-destructive/10 text-destructive border-destructive/20"
                                            : "bg-primary/10 text-primary border-primary/20"
                                        }`}>
                                        {veg.status}
                                    </span>
                                </div>

                                <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
                                    <Clock className="w-4 h-4" />
                                    <span>{new Date(veg.created_at).toLocaleTimeString()}</span>
                                </div>

                                <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                                    <div
                                        className={`h-full transition-all duration-500 ${isProcessing
                                            ? "w-[60%] bg-blue-500/80 animate-[shimmer_2s_infinite]"
                                            : isFailed
                                                ? "w-full bg-destructive"
                                                : "w-full bg-primary"
                                            }`}
                                        style={isProcessing ? {
                                            backgroundImage: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%)',
                                            backgroundSize: '200% 100%'
                                        } : {}}
                                    ></div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </main>

            {/* Registration Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
                    <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-lg sm:p-8 relative animate-in fade-in zoom-in-95 duration-200">
                        <button
                            onClick={closeModal}
                            className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                        >
                            <X className="w-4 h-4" />
                            <span className="sr-only">Close</span>
                        </button>

                        <div className="flex flex-col space-y-1.5 text-center sm:text-left mb-6">
                            <h2 className="text-lg font-semibold leading-none tracking-tight">新しい種の登録</h2>
                            <p className="text-sm text-muted-foreground">
                                種袋の画像をアップロードしてAI分析を開始します。
                            </p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                    種袋の画像
                                </label>
                                <div
                                    className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:bg-accent/50 hover:border-accent transition-colors cursor-pointer"
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    <CloudUpload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                                    <p className="text-sm text-muted-foreground font-medium">{fileName === "Click to browse or drag file here" ? "クリックして選択、またはドラッグ＆ドロップ" : fileName}</p>
                                    <p className="text-xs text-muted-foreground mt-1">対応形式: JPG, PNG</p>
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        accept="image/*"
                                        className="hidden"
                                        onChange={handleFileChange}
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={uploading}
                                className="inline-flex w-full items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-4 py-2"
                            >
                                {uploading ? (
                                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                                ) : (
                                    "登録して分析を開始"
                                )}
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* Detail Modal */}
            {selectedVeg && (
                <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
                    <div className="w-full max-w-3xl rounded-xl border border-border bg-card p-6 shadow-lg sm:p-8 relative flex flex-col max-h-[85vh] animate-in fade-in zoom-in-95 duration-200">
                        <button
                            onClick={closeDetailModal}
                            className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 z-10"
                        >
                            <X className="w-4 h-4" />
                            <span className="sr-only">Close</span>
                        </button>

                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                            <div className="p-2 rounded-lg bg-primary/10">
                                <FlaskConical className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                                <h2 className="text-xl font-semibold">{selectedVeg.name}</h2>
                                <p className="text-sm text-muted-foreground">調査・分析結果</p>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto pr-2 space-y-6">
                            {selectedVeg.instructions ? (
                                <>
                                    <div className="flex justify-end mb-4">
                                        <button
                                            onClick={async () => {
                                                try {
                                                    const res = await fetch(`/api/vegetables/${selectedVeg.id}/select`, {
                                                        method: "POST",
                                                    });
                                                    if (res.ok) {
                                                        alert("エージェントに指示を適用しました！");
                                                    } else {
                                                        alert("エージェントの更新に失敗しました。");
                                                    }
                                                } catch (e) {
                                                    console.error(e);
                                                    alert("エラーが発生しました。");
                                                }
                                            }}
                                            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-green-600 text-white shadow hover:bg-green-700 h-9 px-4 py-2 gap-2"
                                        >
                                            <CloudUpload className="w-4 h-4" />
                                            エージェントに適用
                                        </button>
                                    </div>

                                    {selectedVeg.instructions.volumetric_water_content && (
                                        <div className="rounded-lg border border-border p-4 bg-card/50">
                                            <h3 className="text-sm font-medium text-blue-500 uppercase tracking-wider mb-1">Volumetric Water Content</h3>
                                            <p className="text-2xl font-bold">{selectedVeg.instructions.volumetric_water_content}</p>
                                        </div>
                                    )}

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {Object.entries(selectedVeg.instructions).map(([key, value]) => {
                                            if (key === "original_analysis" || key === "name" || key === "volumetric_water_content") return null;
                                            return (
                                                <div key={key} className="p-4 rounded-lg bg-secondary/20 border border-border/50">
                                                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">{key.replace(/_/g, " ")}</h3>
                                                    <div className="text-sm font-medium break-all">{String(value)}</div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </>
                            ) : (
                                <div className="text-center py-12 text-muted-foreground">
                                    <p>詳細データがありません。</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Footer */}
            <footer className="border-t border-border bg-card mt-auto">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <p className="text-sm text-muted-foreground text-center">© 2025 Smart Farm AI - ハッカソンデモ</p>
                </div>
            </footer>
        </div>
    );
}
