import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './SeedGuide.css';

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

export default function SeedGuide() {
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
    }, []);

    const startPolling = (id: string) => {
        if (pollingRef.current) return;

        pollingRef.current = window.setInterval(async () => {
            try {
                // Use relative path
                const response = await axios.get(`api/seed-guide/jobs/${id}`);
                const status: JobStatus = response.data;
                setJobStatus(status);

                if (status.status === 'COMPLETED') {
                    setSteps(status.result || []);
                    stopPolling();
                    localStorage.removeItem('seedGuideJobId'); // Clear job when done
                } else if (status.status === 'FAILED') {
                    setError(status.message);
                    stopPolling();
                    localStorage.removeItem('seedGuideJobId');
                }
            } catch (err) {
                console.error("Polling error", err);
                // If 404, maybe job expired or server restarted
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
            // Start Async Job
            // Use relative path 'api/...' so it respects the current page's base path
            const response = await axios.post('api/seed-guide/jobs', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            const newJobId = response.data.job_id;
            setJobId(newJobId);
            localStorage.setItem('seedGuideJobId', newJobId);
            startPolling(newJobId);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || "ジョブの開始に失敗しました。");
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
    };

    const isLoading = jobId && (!jobStatus || (jobStatus.status !== 'COMPLETED' && jobStatus.status !== 'FAILED'));

    return (
        <div className="seed-guide-container">
            <h2>AI Planting Guide 🍌 (Async Mode)</h2>

            {/* Input Section */}
            {!steps.length && !isLoading && (
                <div className="upload-section">
                    <p>タネの写真をアップロードしてください。AIが植え方をガイドします。</p>
                    <input type="file" accept="image/*" onChange={handleFileChange} />
                    <button onClick={handleUpload} disabled={!selectedFile}>
                        ガイドを作成 (非同期)
                    </button>
                    {error && <p className="error-msg">{error}</p>}
                </div>
            )}

            {/* Loading / Progress Section */}
            {isLoading && (
                <div className="loading-overlay">
                    <div className="spinner"></div>
                    <p className="loading-status">
                        {jobStatus ? `Status: ${jobStatus.status}` : "Connecting..."}
                    </p>
                    <p className="loading-message">
                        {jobStatus?.message || "AIが分析中...画面を閉じても処理は続きます。"}
                    </p>
                    <button className="cancel-btn" onClick={handleReset}>キャンセル</button>
                </div>
            )}

            {/* Result Section (Wizard) */}
            {steps.length > 0 && (
                <div className="wizard-container">
                    <div className="step-indicator">
                        Step {currentStepIndex + 1} / {steps.length}
                    </div>

                    <div className="step-content">
                        <h3>{steps[currentStepIndex].title}</h3>

                        <div className="step-image-container">
                            {steps[currentStepIndex].image_base64 ? (
                                <img
                                    src={`data:image/jpeg;base64,${steps[currentStepIndex].image_base64}`}
                                    alt={steps[currentStepIndex].title}
                                    className="step-image"
                                />
                            ) : (
                                <div className="no-image">
                                    {steps[currentStepIndex].error ? "画像生成エラー" : "画像なし"}
                                </div>
                            )}
                        </div>

                        <p className="step-description">{steps[currentStepIndex].description}</p>
                    </div>

                    <div className="navigation-buttons">
                        <button onClick={handlePrev} disabled={currentStepIndex === 0}>
                            戻る
                        </button>
                        <button onClick={handleReset} style={{ marginLeft: '10px', backgroundColor: '#555' }}>
                            最初から
                        </button>
                        <button onClick={handleNext} disabled={currentStepIndex === steps.length - 1} style={{ marginLeft: '10px' }}>
                            次へ
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
