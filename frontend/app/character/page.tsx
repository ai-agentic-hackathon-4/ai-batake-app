"use client"

import React, { useState, useEffect, useRef } from 'react';
import { Upload, ArrowLeft, RefreshCw, Sprout, Sparkles, Loader2 } from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card"
import Link from 'next/link';
import { cn } from "@/lib/utils";

interface CharacterResult {
    name: string;
    character_name: string;
    personality: string;
    image_base64: string;
}

interface JobStatus {
    status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
    message: string;
    result?: CharacterResult;
}

export default function CharacterPage() {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [jobId, setJobId] = useState<string | null>(null);
    const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
    const [character, setCharacter] = useState<CharacterResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Animation states
    const [animationStage, setAnimationStage] = useState<'idle' | 'seed-shaking' | 'sprouting' | 'blooming'>('idle');

    // Polling interval ref
    const pollingRef = useRef<number | null>(null);

    useEffect(() => {
        return () => {
            if (previewUrl) URL.revokeObjectURL(previewUrl);
            stopPolling();
        };
    }, []);

    // Watch status to trigger animations
    useEffect(() => {
        if (!jobStatus) return;

        if (jobStatus.status === 'PROCESSING' && animationStage === 'seed-shaking') {
            // Transition to sprouting after a delay or condition
            const timer = setTimeout(() => setAnimationStage('sprouting'), 3000);
            return () => clearTimeout(timer);
        }

        if (jobStatus.status === 'COMPLETED' && character) {
            setAnimationStage('blooming');
            stopPolling();
        }
    }, [jobStatus, character]);

    const startPolling = (id: string) => {
        if (pollingRef.current) return;

        pollingRef.current = window.setInterval(async () => {
            try {
                const response = await fetch(`/api/seed-guide/jobs/${id}`);
                if (!response.ok) {
                    if (response.status !== 404) throw new Error(`Polling failed: ${response.statusText}`);
                    return;
                }

                const status: JobStatus = await response.json();
                setJobStatus(status);

                if (status.status === 'COMPLETED') {
                    setCharacter(status.result as CharacterResult);
                    // Animation transition is handled in useEffect
                } else if (status.status === 'FAILED') {
                    setError(status.message);
                    setAnimationStage('idle');
                    stopPolling();
                }
            } catch (err) {
                console.error("Polling error", err);
                stopPolling();
                setError("通信エラーが発生しました");
                setAnimationStage('idle');
            }
        }, 2000);
    };

    const stopPolling = () => {
        if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
        }
    };

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            const file = event.target.files[0];
            setSelectedFile(file);
            setPreviewUrl(URL.createObjectURL(file));
            setError(null);
        }
    };

    const handleGenerate = async () => {
        if (!selectedFile) return;

        setError(null);
        setCharacter(null);
        setJobStatus({ status: 'PENDING', message: 'Starting...' });
        setAnimationStage('seed-shaking'); // Start animation

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/api/seed-guide/character', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Upload failed");
            }

            const data = await response.json();
            setJobId(data.job_id);
            startPolling(data.job_id);
        } catch (err: any) {
            setError(err.message || "エラーが発生しました");
            setAnimationStage('idle');
        }
    };

    const handleReset = () => {
        stopPolling();
        setSelectedFile(null);
        if (previewUrl) URL.revokeObjectURL(previewUrl);
        setPreviewUrl(null);
        setJobId(null);
        setJobStatus(null);
        setCharacter(null);
        setAnimationStage('idle');
        setError(null);
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-green-50 to-background flex flex-col font-sans">
            {/* Header */}
            <header className="border-b border-border/50 bg-white/50 backdrop-blur-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Link href="/" className="mr-2 p-2 hover:bg-green-100 rounded-full transition-colors">
                            <ArrowLeft className="h-5 w-5 text-green-700" />
                        </Link>
                        <div className="p-2 rounded-xl bg-gradient-to-br from-green-400 to-emerald-600 shadow-md">
                            <Sparkles className="h-6 w-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-gray-800 tracking-tight">AI Character Maker</h1>
                            <p className="text-xs text-green-600 font-medium">種から生まれる不思議なお友達</p>
                        </div>
                    </div>
                </div>
            </header>

            <main className="flex-1 w-full max-w-4xl mx-auto px-6 py-12 flex flex-col items-center justify-center min-h-[600px]">

                {/* IDLE State: Upload */}
                {animationStage === 'idle' && (
                    <div className="w-full max-w-md animate-in fade-in zoom-in duration-500">
                        <Card className="border-2 border-dashed border-green-200 bg-white/80 shadow-xl overflow-hidden">
                            <CardContent className="pt-10 pb-10 flex flex-col items-center text-center space-y-8">
                                <div className="space-y-4">
                                    <div className="mx-auto w-24 h-24 bg-green-100 rounded-full flex items-center justify-center relative group cursor-pointer transition-transform hover:scale-105">
                                        <Upload className="h-10 w-10 text-green-600" />
                                        <input
                                            type="file"
                                            accept="image/*"
                                            className="absolute inset-0 opacity-0 cursor-pointer"
                                            onChange={handleFileChange}
                                        />
                                    </div>
                                    <div>
                                        <h2 className="text-2xl font-bold text-gray-800">写真をアップロード</h2>
                                        <p className="text-gray-500 mt-2">種の袋や野菜の写真をみせてね</p>
                                    </div>
                                </div>

                                {previewUrl && (
                                    <div className="relative w-48 h-48 rounded-2xl overflow-hidden border-4 border-white shadow-lg rotate-2">
                                        <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />
                                    </div>
                                )}

                                <button
                                    onClick={handleGenerate}
                                    disabled={!selectedFile}
                                    className="w-full py-4 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold text-lg shadow-lg shadow-green-200/50 disabled:opacity-50 disabled:shadow-none hover:shadow-xl hover:scale-[1.02] transition-all"
                                >
                                    キャラクターを生み出す！
                                </button>

                                {error && (
                                    <p className="text-red-500 text-sm bg-red-50 px-4 py-2 rounded-lg">{error}</p>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* ANIMATION STAGES */}
                {animationStage !== 'idle' && animationStage !== 'blooming' && (
                    <div className="flex flex-col items-center justify-center space-y-8 animate-in fade-in">
                        <div className="relative w-64 h-64 flex items-center justify-center">

                            {/* Stage 1: Seed Shaking (Analyzing) */}
                            {animationStage === 'seed-shaking' && previewUrl && (
                                <div className="relative animate-bounce-custom">
                                    {/* Using custom class or standard tailwind animations. Let's use standard bounce for now but maybe customize later if needed */}
                                    <div className="w-32 h-32 rounded-full border-4 border-white shadow-2xl overflow-hidden animate-[wiggle_1s_ease-in-out_infinite]">
                                        <img src={previewUrl} className="w-full h-full object-cover opacity-80" />
                                    </div>
                                    <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-4xl animate-pulse">
                                        🌱
                                    </div>
                                </div>
                            )}

                            {/* Stage 2: Sprouting (Generating) */}
                            {animationStage === 'sprouting' && (
                                <div className="relative">
                                    <div className="absolute inset-0 bg-green-400 rounded-full blur-3xl opacity-20 animate-pulse"></div>
                                    <Sprout className="w-32 h-32 text-green-500 animate-[bounce_3s_infinite]" />
                                    <div className="absolute -top-12 -right-12">
                                        <Sparkles className="w-12 h-12 text-yellow-400 animate-spin-slow" />
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="text-center space-y-2">
                            <h3 className="text-2xl font-bold text-gray-800 animate-pulse">
                                {animationStage === 'seed-shaking' ? "種を鑑定中..." : "エネルギーを充填中..."}
                            </h3>
                            <p className="text-gray-500">
                                {jobStatus?.message || "AIが一生懸命考えています"}
                            </p>
                            {/* Progress bar simulation */}
                            <div className="w-64 h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div className="h-full bg-green-500 animate-[width-grow_10s_linear_infinite]" style={{ width: animationStage === 'sprouting' ? '90%' : '30%' }}></div>
                            </div>
                        </div>
                    </div>
                )}

                {/* FINAL STAGE: BLOOMING (Result) */}
                {character && animationStage === 'blooming' && (
                    <div className="w-full max-w-lg perspective-1000">
                        <Card className="bg-white/90 backdrop-blur border-none shadow-2xl overflow-hidden animate-in zoom-in-50 duration-700 spring-bounce-effect">
                            {/* Dynamic background based on veggie name? For now just gradient */}
                            <div className="absolute inset-0 bg-gradient-to-br from-yellow-100/50 via-transparent to-green-100/50 opacity-50"></div>

                            <CardContent className="pt-12 pb-12 flex flex-col items-center text-center relative z-10">

                                <div className="relative mb-8 group">
                                    {/* Shining effect behind */}
                                    <div className="absolute inset-0 bg-yellow-400 rounded-full blur-2xl opacity-0 group-hover:opacity-40 transition-opacity duration-1000 animate-pulse"></div>

                                    <div className="relative w-64 h-64 rounded-3xl overflow-hidden border-8 border-white shadow-2xl rotate-3 transform transition-transform hover:rotate-0 hover:scale-105 duration-300">
                                        <img
                                            src={`data:image/jpeg;base64,${character.image_base64}`}
                                            alt={character.character_name}
                                            className="w-full h-full object-cover"
                                        />
                                    </div>
                                    <div className="absolute -bottom-6 -right-6 bg-white p-3 rounded-full shadow-lg rotate-12 animate-[bounce_2s_infinite]">
                                        <span className="text-4xl">✨</span>
                                    </div>
                                </div>

                                <div className="space-y-6 max-w-sm">
                                    <div>
                                        <p className="text-green-600 font-bold tracking-widest uppercase text-sm mb-1">{character.name}の妖精</p>
                                        <h2 className="text-4xl font-black text-gray-800 tracking-tight drop-shadow-sm">
                                            {character.character_name}
                                        </h2>
                                    </div>

                                    <div className="bg-white/80 p-6 rounded-2xl shadow-sm border border-green-100">
                                        <p className="text-lg text-gray-600 font-medium leading-relaxed italic">
                                            "{character.personality}"
                                        </p>
                                    </div>
                                </div>

                                <div className="mt-10">
                                    <button
                                        onClick={handleReset}
                                        className="inline-flex items-center justify-center px-8 py-3 rounded-full bg-gray-900 text-white font-bold hover:bg-gray-800 transition-all gap-2 shadow-lg hover:shadow-xl transform hover:-translate-y-1"
                                    >
                                        <RefreshCw className="h-4 w-4" /> もう一度あそぶ
                                    </button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

            </main>

            <style jsx global>{`
                @keyframes wiggle {
                    0%, 100% { transform: rotate(-3deg); }
                    50% { transform: rotate(3deg); }
                }
                @keyframes spin-slow {
                    to { transform: rotate(360deg); }
                }
                .spring-bounce-effect {
                    animation-timing-function: cubic-bezier(0.34, 1.56, 0.64, 1);
                }
            `}</style>
        </div>
    );
}
