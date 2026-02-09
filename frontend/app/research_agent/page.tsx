"use client";

import { useEffect, useState, useRef } from "react";
import { Leaf, Plus, CloudUpload, Clock, X, FlaskConical, Droplets, Thermometer, Sun, Sprout, Check, Send, AlertCircle, ArrowRight, ArrowLeft, Search, ExternalLink } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import Link from "next/link";

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
    const [applyingToAgent, setApplyingToAgent] = useState(false);
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
                fetchVegetables();
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

    const handleApplyToAgent = async () => {
        if (!selectedVeg) return;
        setApplyingToAgent(true);
        try {
            const res = await fetch(`/api/vegetables/${selectedVeg.id}/select`, {
                method: "POST",
            });
            if (res.ok) {
                alert("Instructions applied to edge agent!");
            } else {
                alert("Failed to apply instructions.");
            }
        } catch (e) {
            console.error(e);
            alert("An error occurred.");
        } finally {
            setApplyingToAgent(false);
        }
    };

    const handleDeleteVegetable = async (id: string) => {
        if (!confirm("このリサーチデータを削除しますか？")) return;
        try {
            const res = await fetch(`/api/vegetables/${id}`, { method: "DELETE" });
            if (!res.ok) throw new Error("Delete failed");
            if (selectedVeg?.id === id) setSelectedVeg(null);
            fetchVegetables();
        } catch (e) {
            console.error(e);
            alert("削除に失敗しました");
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

    // Helper to format instruction keys
    const formatKey = (key: string) => {
        return key
            .replace(/_/g, " ")
            .replace(/([A-Z])/g, ' $1')
            .replace(/^./, str => str.toUpperCase());
    };

    // Helper to clean values
    const formatValue = (value: any) => {
        if (typeof value === 'object') return JSON.stringify(value);
        return String(value);
    }

    // Categorize instructions
    const categorizeInstructions = (instructions: Record<string, any>) => {
        const categories = {
            care: { icon: Sprout, label: "Cultivation & Care", color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-100", items: [] as [string, any][] },
            environment: { icon: Thermometer, label: "Environment", color: "text-orange-600", bg: "bg-orange-50", border: "border-orange-100", items: [] as [string, any][] },
            water_soil: { icon: Droplets, label: "Water & Soil", color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-100", items: [] as [string, any][] },
        };

        Object.entries(instructions).forEach(([key, value]) => {
            if (key === "original_analysis" || key === "name" || key === "volumetric_water_content" || key === "description") return;

            const lowerKey = key.toLowerCase();
            if (lowerKey.includes("water") || lowerKey.includes("soil") || lowerKey.includes("moisture") || lowerKey.includes("ph")) {
                categories.water_soil.items.push([key, value]);
            } else if (lowerKey.includes("temp") || lowerKey.includes("light") || lowerKey.includes("sun") || lowerKey.includes("humidity") || lowerKey.includes("wind")) {
                categories.environment.items.push([key, value]);
            } else {
                categories.care.items.push([key, value]);
            }
        });

        return categories;
    };

    // Custom Gauge Component for VWC - Clean & Simple
    const VWCGauge = ({ value }: { value: string }) => {
        const numMatch = value.match(/(\d+)/);
        const percentage = numMatch ? Math.min(Math.max(parseInt(numMatch[0]), 0), 100) : 50;

        const data = [
            { name: 'Value', value: percentage },
            { name: 'Remaining', value: 100 - percentage },
        ];
        const COLORS = ['#3b82f6', '#e2e8f0']; // Blue-500 & Slate-200

        return (
            <div className="h-24 w-full relative flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            startAngle={180}
                            endAngle={0}
                            innerRadius={45}
                            outerRadius={60}
                            paddingAngle={2}
                            dataKey="value"
                            stroke="none"
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                    </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-center pt-8">
                    <span className="text-xl font-bold text-slate-900">{percentage}%</span>
                </div>
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-background flex flex-col font-sans text-foreground">
            {/* Header - Consistent with Dashboard */}
            <header className="border-b border-border bg-card">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-3">
                            <Link href="/" className="mr-2 p-1 hover:bg-accent rounded-full transition-colors">
                                <ArrowLeft className="h-5 w-5 text-muted-foreground" />
                            </Link>
                            <div className="p-2 rounded-lg bg-primary/10">
                                <FlaskConical className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                                <h1 className="text-xl font-semibold text-card-foreground">リサーチエージェント</h1>
                                <p className="text-sm text-muted-foreground">AIによる栽培情報の深層調査</p>
                            </div>
                        </div>
                        <div className={`px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-2 border ${isSystemExecuting
                            ? "bg-blue-50 text-blue-600 border-blue-200"
                            : "bg-primary/10 text-primary border-primary/20"
                            }`}>
                            <div className={`w-2 h-2 rounded-full ${isSystemExecuting ? "bg-blue-500 animate-pulse" : "bg-primary"}`}></div>
                            {isSystemExecuting ? "EXECUTING RESEARCH..." : "SYSTEM IDLE"}
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full">
                <div className="flex justify-between items-center mb-8">
                    <h2 className="text-2xl font-bold tracking-tight">Vegetable Research</h2>
                    <button
                        onClick={openModal}
                        className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2 gap-2"
                    >
                        <Plus className="w-4 h-4" />
                        新しい種を登録
                    </button>
                </div>

                {/* Empty State */}
                {vegetables.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 text-center bg-card rounded-lg border border-dashed border-border px-4">
                        <div className="p-4 rounded-full bg-muted mb-4">
                            <FlaskConical className="h-8 w-8 text-muted-foreground" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2">No Research Data Yet</h3>
                        <p className="text-muted-foreground mb-6 max-w-sm">
                            Upload a seed packet image to start AI-powered deep research and get optimal growing instructions.
                        </p>
                        <button
                            onClick={openModal}
                            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-6 gap-2"
                        >
                            <Plus className="w-4 h-4" />
                            Register Your First Seed
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {vegetables.map((veg) => {
                            const isProcessing = veg.status === "processing";
                            const isFailed = veg.status === "failed";

                            return (
                                <div
                                    key={veg.id}
                                    className={`group relative rounded-xl border bg-card p-5 shadow-sm transition-all hover:shadow-md cursor-pointer ${selectedVeg?.id === veg.id ? 'border-primary ring-1 ring-primary' : 'border-border hover:border-primary/50'
                                        }`}
                                    onClick={() => !isProcessing && setSelectedVeg(veg)}
                                >
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteVegetable(veg.id);
                                        }}
                                        className="absolute top-3 right-3 text-xs text-red-500 hover:text-red-600"
                                    >
                                        削除
                                    </button>
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-lg ${isProcessing ? "bg-amber-100 text-amber-600" :
                                                isFailed ? "bg-red-100 text-red-600" :
                                                    "bg-primary/10 text-primary"
                                                }`}>
                                                {isProcessing ? <Clock className="h-5 w-5" /> :
                                                    isFailed ? <AlertCircle className="h-5 w-5" /> :
                                                        <Sprout className="h-5 w-5" />}
                                            </div>
                                            <div className="overflow-hidden">
                                                <h3 className="font-semibold text-lg leading-none truncate">{veg.name}</h3>
                                                <p className="text-xs text-muted-foreground mt-1 truncate">ID: {veg.id.substring(0, 8)}</p>
                                            </div>
                                        </div>
                                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${isProcessing ? "bg-amber-50 text-amber-600 border-amber-200" :
                                            isFailed ? "bg-red-50 text-red-600 border-red-200" :
                                                "bg-blue-50 text-blue-600 border-blue-200"
                                            }`}>
                                            {isProcessing ? "ANALYZING" : isFailed ? "FAILED" : "READY"}
                                        </span>
                                    </div>

                                    {/* Progress Bar for Processing - Moved Inside Content */}
                                    {isProcessing && (
                                        <div className="mt-4 w-full h-1.5 bg-amber-100 rounded-full overflow-hidden">
                                            <div className="h-full bg-amber-500 w-1/2 animate-[shimmer_2s_infinite]"></div>
                                        </div>
                                    )}

                                    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-4">
                                        <Clock className="w-3 h-3" />
                                        <span>{new Date(veg.created_at).toLocaleDateString()}</span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>

            {/* Registration Modal - Simple & Clean */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
                    <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-lg relative animate-in fade-in zoom-in-95 duration-200">
                        <button
                            onClick={closeModal}
                            className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100 transition-opacity"
                        >
                            <X className="w-4 h-4" />
                            <span className="sr-only">Close</span>
                        </button>

                        <div className="mb-6">
                            <h2 className="text-xl font-semibold">New Seed Analysis</h2>
                            <p className="text-sm text-muted-foreground mt-1">
                                Upload a seed packet image for AI analysis.
                            </p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div
                                className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:bg-muted/50 hover:border-primary/50 transition-all cursor-pointer"
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <CloudUpload className="mx-auto h-10 w-10 text-muted-foreground mb-4" />
                                <p className="text-sm font-medium">{fileName}</p>
                                <p className="text-xs text-muted-foreground mt-1">JPG, PNG supported</p>
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    accept="image/*"
                                    className="hidden"
                                    onChange={handleFileChange}
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={uploading}
                                className="w-full inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-4 py-2"
                            >
                                {uploading ? "Analyzing..." : "Start Analysis"}
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* Detail Modal - Centered Popup */}
            {selectedVeg && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
                    <div className="absolute inset-0 bg-background/80 backdrop-blur-sm transition-opacity" onClick={closeDetailModal} />
                    <div className="w-full max-w-3xl max-h-[90vh] bg-card border border-border shadow-2xl rounded-2xl relative flex flex-col animate-in fade-in zoom-in-95 duration-200">

                        {/* Detail Header */}
                        <div className="px-6 py-5 border-b border-border flex items-center justify-between bg-card sticky top-0 z-10 rounded-t-2xl">
                            <div className="flex items-center gap-4">
                                <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                                    <FlaskConical className="h-6 w-6" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold tracking-tight">{selectedVeg.name}</h2>
                                    <p className="text-sm text-muted-foreground">AI Analysis Result</p>
                                </div>
                            </div>
                            <button
                                onClick={closeDetailModal}
                                className="p-2 hover:bg-muted rounded-full transition-colors"
                            >
                                <X className="w-5 h-5 text-muted-foreground" />
                            </button>
                        </div>

                        {/* Content Scroll Area */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-8">
                            {selectedVeg.instructions ? (
                                <>
                                    {/* Action Banner */}
                                    <div className="flex flex-col sm:flex-row items-center justify-between bg-muted/40 p-5 rounded-xl border border-border gap-4">
                                        <div>
                                            <p className="text-base font-semibold">Ready to Deploy</p>
                                            <p className="text-sm text-muted-foreground">Sync these environmental parameters to your edge device.</p>
                                        </div>
                                        <button
                                            onClick={handleApplyToAgent}
                                            disabled={applyingToAgent}
                                            className="w-full sm:w-auto px-6 py-2.5 rounded-lg bg-green-600 text-white text-sm font-bold hover:bg-green-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-70 shadow-sm"
                                        >
                                            {applyingToAgent ? (
                                                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                                            ) : (
                                                <>
                                                    <Send className="w-4 h-4" /> Apply Config
                                                </>
                                            )}
                                        </button>
                                    </div>

                                    {/* VWC Gauge Section */}
                                    {selectedVeg.instructions.volumetric_water_content && (
                                        <div className="bg-card rounded-xl p-6 border border-border shadow-sm flex items-center justify-between">
                                            <div>
                                                <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Target Soil Moisture</h3>
                                                <p className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-blue-400">
                                                    {selectedVeg.instructions.volumetric_water_content}
                                                </p>
                                                <p className="text-sm text-muted-foreground mt-1 font-medium">Volumetric Water Content (VWC)</p>
                                            </div>
                                            <div className="w-32 h-32">
                                                <VWCGauge value={selectedVeg.instructions.volumetric_water_content} />
                                            </div>
                                        </div>
                                    )}

                                    {/* Description/Summary */}
                                    {selectedVeg.instructions.description && (
                                        <div className="bg-muted/20 p-6 rounded-xl border border-border">
                                            <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
                                                <AlertCircle className="w-4 h-4 text-primary" /> Overview
                                            </h3>
                                            <p className="text-sm text-muted-foreground leading-relaxed">
                                                {selectedVeg.instructions.description}
                                            </p>
                                        </div>
                                    )}

                                    {/* Categorized Info */}
                                    <div className="space-y-6">
                                        {(() => {
                                            const categories = categorizeInstructions(selectedVeg.instructions);
                                            return Object.entries(categories).map(([key, category]) => {
                                                if (category.items.length === 0) return null;
                                                const Icon = category.icon;

                                                return (
                                                    <div key={key} className="rounded-xl border border-border bg-card overflow-hidden shadow-sm">
                                                        <div className="px-5 py-3 bg-muted/30 border-b border-border flex items-center gap-3">
                                                            <Icon className={`h-5 w-5 ${category.color.replace('text-', 'text-opacity-90 ')}`} />
                                                            <h3 className="text-base font-bold text-card-foreground">{category.label}</h3>
                                                        </div>
                                                        <div className="p-5 space-y-4">
                                                            {category.items.map(([k, v]) => (
                                                                <div key={k} className="grid grid-cols-1 sm:grid-cols-[160px_1fr] gap-2 sm:gap-8 border-b border-border/50 pb-4 last:border-0 last:pb-0 items-start">
                                                                    <span className="text-xs font-bold text-muted-foreground uppercase tracking-wide break-words pt-1 text-right sm:text-left">{formatKey(k)}</span>
                                                                    <span className="text-sm font-medium text-foreground leading-relaxed">{formatValue(v)}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                );
                                            });
                                        })()}
                                    </div>
                                </>
                            ) : (
                                <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
                                    <FlaskConical className="h-16 w-16 mb-4 opacity-20" />
                                    <p className="text-lg font-medium">No detailed data available.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
            <style jsx global>{`
                @keyframes shimmer {
                    0% { transform: translateX(-100%); }
                    100% { transform: translateX(100%); }
                }
            `}</style>
        </div>
    );
}
