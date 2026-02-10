"use client";

import React from "react";
import { ExternalLink, Search } from "lucide-react";

interface GroundingMetadata {
    searchEntryPoint?: {
        renderedContent?: string;
    };
    groundingChunks?: Array<{
        web?: {
            uri?: string;
            title?: string;
        };
    }>;
    groundingSupports?: Array<{
        segment?: {
            startIndex?: number;
            endIndex?: number;
            text?: string;
        };
        groundingChunkIndices?: number[];
        confidenceScores?: number[];
    }>;
}

interface GroundingDisplayProps {
    metadata?: GroundingMetadata;
    className?: string;
}

export function GroundingDisplay({ metadata, className = "" }: GroundingDisplayProps) {
    if (!metadata) return null;

    const { searchEntryPoint, groundingChunks } = metadata;

    return (
        <div className={`space-y-4 pt-4 border-t border-slate-200 mt-6 ${className}`}>
            {/* Search Entry Point (The "Search with Google" chip) */}
            {searchEntryPoint?.renderedContent && (
                <div
                    className="google-grounding-entry-point"
                    dangerouslySetInnerHTML={{ __html: searchEntryPoint.renderedContent }}
                />
            )}

            {/* Citations / Sources section */}
            {groundingChunks && groundingChunks.length > 0 && (
                <div className="space-y-2">
                    <h4 className="text-sm font-semibold text-slate-600 flex items-center gap-2">
                        <Search className="h-3.5 w-3.5" /> 出典・参考文献
                    </h4>
                    <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {groundingChunks.map((chunk, idx) => (
                            chunk.web && (
                                <li key={idx} className="text-xs">
                                    <a
                                        href={chunk.web.uri}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-1.5 p-2 rounded bg-slate-50 hover:bg-slate-100 text-slate-600 hover:text-blue-600 transition-colors border border-slate-200"
                                    >
                                        <ExternalLink className="h-3 w-3 flex-shrink-0" />
                                        <span className="truncate font-medium">{chunk.web.title || chunk.web.uri}</span>
                                    </a>
                                </li>
                            )
                        ))}
                    </ul>
                </div>
            )}

            <p className="text-[10px] text-slate-400 italic">
                * Google 検索結果に基づいた情報が含まれています。
            </p>
        </div>
    );
}
