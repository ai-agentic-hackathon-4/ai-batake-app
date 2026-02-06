"use client";

import { useEffect, useState } from "react";
import { Sprout, Database, Cpu, PenTool } from "lucide-react";

interface LoadingProps {
    statusMessage?: string;
}

export function DiaryGenerationLoading({ statusMessage }: LoadingProps) {
    const [step, setStep] = useState(0);

    const steps = [
        {
            icon: Database,
            text: "センサーデータを収集中...",
            color: "text-blue-500",
        },
        {
            icon: Sprout,
            text: "生育状況を分析中...",
            color: "text-green-500",
        },
        {
            icon: Cpu,
            text: "AIがインサイトを抽出中...",
            color: "text-purple-500",
        },
        {
            icon: PenTool,
            text: "成長記録を執筆中...",
            color: "text-orange-500",
        },
    ];

    useEffect(() => {
        const interval = setInterval(() => {
            setStep((prev) => (prev + 1) % steps.length);
        }, 2000);
        return () => clearInterval(interval);
    }, []);

    const CurrentIcon = steps[step].icon;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
            <div className="flex flex-col items-center gap-6 p-8 rounded-xl bg-card border border-border shadow-2xl max-w-sm w-full animate-in fade-in zoom-in duration-300">
                {/* Icon Animation */}
                <div className="relative">
                    <div className="absolute inset-0 rounded-full animate-ping opacity-20 bg-primary" />
                    <div className={`p-4 rounded-full bg-accent/10 ${steps[step].color}`}>
                        <CurrentIcon className="w-12 h-12 animate-pulse" />
                    </div>
                </div>

                {/* Text and Progress */}
                <div className="space-y-2 text-center w-full">
                    <h3 className="text-lg font-semibold animate-pulse">
                        日記を生成しています
                    </h3>
                    <p className="text-muted-foreground transition-all duration-300 min-h-[1.5rem]">
                        {statusMessage || steps[step].text}
                    </p>

                    {/* Progress Indicator */}
                    <div className="flex justify-center gap-2 mt-4">
                        {steps.map((_, i) => (
                            <div
                                key={i}
                                className={`h-1.5 rounded-full transition-all duration-300 ${i === step
                                    ? "w-8 bg-primary"
                                    : "w-2 bg-primary/20"
                                    }`}
                            />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
