"use client"

import React, { useState, useEffect, useRef } from 'react';
import { Upload, ArrowLeft, ArrowRight, RotateCcw, Sprout, AlertCircle, Loader2 } from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card"
import Link from 'next/link';

interface Step {
    title: string;
    description: string;
    image_base64: string | null;
    error?: string;
}

interface JobStatus {
    status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
    message: string;
    result?: Step[];
}

export default function SeedGuidePage() {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [jobId, setJobId] = useState<string | null>(null);
    const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
    const [steps, setSteps] = useState<Step[]>([]);
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [error, setError] = useState<string | null>(null);

    // Polling interval ref
    const pollingRef = useRef<number | null>(null);

    // Restore job from localStorage on mount
    useEffect(() => {
        const storedJobId = localStorage.getItem('seedGuideJobId');
        if (storedJobId) {
            console.log("Restoring active job:", storedJobId);
            setJobId(storedJobId);
            startPolling(storedJobId);
        }
        return () => stopPolling();
    }, []);

    const startPolling = (id: string) => {
        if (pollingRef.current) return;

        pollingRef.current = window.setInterval(async () => {
            try {
                const response = await fetch(`/api/seed-guide/jobs/${id}`);

                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error("Job not found");
                    }
                    throw new Error(`Polling failed: ${response.statusText}`);
                }

                const status: JobStatus = await response.json();
                setJobStatus(status);

                if (status.status === 'COMPLETED') {
                    setSteps(status.result || []);
                    stopPolling();
                    localStorage.removeItem('seedGuideJobId');
                } else if (status.status === 'FAILED') {
                    setError(status.message);
                    stopPolling();
                    localStorage.removeItem('seedGuideJobId');
                }
            } catch (err) {
                console.error("Polling error", err);
                stopPolling();
                localStorage.removeItem('seedGuideJobId');
                setError("ジョブが見つかりません。");
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
            setSelectedFile(event.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        setError(null);
        setSteps([]);
        setCurrentStepIndex(0);
        setJobStatus(null);

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/api/seed-guide/jobs', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Upload failed");
            }

            const data = await response.json();
            const newJobId = data.job_id;
            setJobId(newJobId);
            localStorage.setItem('seedGuideJobId', newJobId);
            startPolling(newJobId);
        } catch (err: any) {
            console.error(err);
            setError(err.message || "ジョブの開始に失敗しました。");
        }
    };

    const handleNext = () => {
        if (currentStepIndex < steps.length - 1) {
            setCurrentStepIndex(prev => prev + 1);
        }
    };

    const handlePrev = () => {
        if (currentStepIndex > 0) {
            setCurrentStepIndex(prev => prev - 1);
        }
    };

    const handleReset = () => {
        stopPolling();
        setSteps([]);
        setJobId(null);
        setJobStatus(null);
        setSelectedFile(null);
        setCurrentStepIndex(0);
        localStorage.removeItem('seedGuideJobId');
        setError(null);
    };

    const isLoading = jobId && (!jobStatus || (jobStatus.status !== 'COMPLETED' && jobStatus.status !== 'FAILED'));

    return (
        <div className="min-h-screen bg-background flex flex-col">
            {/* Header */}
            <header className="border-b border-border bg-card">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Link href="/" className="mr-2 p-1 hover:bg-accent rounded-full transition-colors">
                            <ArrowLeft className="h-5 w-5 text-muted-foreground" />
                        </Link>
                        <div className="p-2 rounded-lg bg-primary/10">
                            <Sprout className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold text-card-foreground">Seed Guide</h1>
                            <p className="text-sm text-muted-foreground">AI Planting Assistant</p>
                        </div>
                    </div>
                </div>
            </header>

            <main className="flex-1 max-w-7xl mx-auto px-6 py-8 w-full">

                {/* Input Section */}
                {!steps.length && !isLoading && (
                    <div className="max-w-2xl mx-auto">
                        <div className="text-center mb-8">
                            <h2 className="text-2xl font-semibold tracking-tight">Create New Guide</h2>
                            <p className="text-muted-foreground mt-2">Upload a seed packet photo to generate a step-by-step growing plan.</p>
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
                                        Create Guide (Async)
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

                {/* Loading Section */}
                {isLoading && (
                    <div className="max-w-2xl mx-auto">
                        <Card>
                            <CardContent className="pt-12 pb-12 flex flex-col items-center text-center space-y-6">
                                <Loader2 className="h-12 w-12 text-primary animate-spin" />
                                <div className="space-y-2">
                                    <h2 className="text-xl font-semibold">AI is Analyzing...</h2>
                                    <p className="text-muted-foreground">
                                        {jobStatus?.message || "Identifying seed type and generating guide..."}
                                    </p>
                                    <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary">
                                        Status: {jobStatus?.status || "Connecting..."}
                                    </div>
                                </div>
                                <button
                                    className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-9 px-4 py-2"
                                    onClick={handleReset}
                                >
                                    Cancel
                                </button>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* Result Wizard */}
                {steps.length > 0 && (
                    <div className="max-w-3xl mx-auto space-y-6">
                        <div className="flex justify-between items-center text-sm text-muted-foreground">
                            <span className="font-medium">Step {currentStepIndex + 1} of {steps.length}</span>
                            <div className="flex gap-1">
                                {steps.map((_, idx) => (
                                    <div
                                        key={idx}
                                        className={`h-1.5 w-8 rounded-full transition-colors ${idx <= currentStepIndex ? 'bg-primary' : 'bg-muted'}`}
                                    />
                                ))}
                            </div>
                        </div>

                        <Card className="overflow-hidden border-border shadow-sm">
                            <div className="aspect-video bg-muted relative flex items-center justify-center border-b border-border">
                                {steps[currentStepIndex].image_base64 ? (
                                    <img
                                        src={`data:image/jpeg;base64,${steps[currentStepIndex].image_base64}`}
                                        alt={steps[currentStepIndex].title}
                                        className="w-full h-full object-cover"
                                    />
                                ) : (
                                    <div className="flex flex-col items-center text-muted-foreground">
                                        <Sprout className="h-12 w-12 mb-2 opacity-20" />
                                        <span>No Visual Available</span>
                                    </div>
                                )}
                            </div>
                            <CardContent className="pt-6 space-y-4">
                                <h3 className="text-2xl font-bold tracking-tight">{steps[currentStepIndex].title}</h3>
                                <div className="h-px w-full bg-border" />
                                <p className="text-lg leading-relaxed text-muted-foreground">
                                    {steps[currentStepIndex].description}
                                </p>
                            </CardContent>
                        </Card>

                        <div className="flex justify-between pt-4">
                            <button
                                onClick={handlePrev}
                                disabled={currentStepIndex === 0}
                                className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2 gap-2"
                            >
                                <ArrowLeft className="h-4 w-4" /> Back
                            </button>

                            <div className="flex gap-3">
                                <button
                                    onClick={handleReset}
                                    className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80 h-10 px-4 py-2 gap-2"
                                >
                                    <RotateCcw className="h-4 w-4" /> Restart
                                </button>
                                <button
                                    onClick={handleNext}
                                    disabled={currentStepIndex === steps.length - 1}
                                    className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-4 py-2 gap-2"
                                >
                                    Next <ArrowRight className="h-4 w-4" />
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </main>

            <footer className="border-t border-border bg-card">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <p className="text-sm text-muted-foreground text-center">© 2025 Smart Farm AI - ハッカソンデモ</p>
                </div>
            </footer>
        </div>
    );
}
