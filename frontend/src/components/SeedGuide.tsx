import React, { useState } from 'react';
import axios from 'axios';
import './SeedGuide.css';

interface Step {
    title: string;
    description: string;
    image_base64: string | null;
    error?: string;
}

export default function SeedGuide() {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [steps, setSteps] = useState<Step[]>([]);
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [error, setError] = useState<string | null>(null);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            setSelectedFile(event.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        setLoading(true);
        setError(null);
        setSteps([]);
        setCurrentStepIndex(0);

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await axios.post('/api/seed-guide', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setSteps(response.data.steps);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || "ガイドの生成に失敗しました。");
        } finally {
            setLoading(false);
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
        setSteps([]);
        setSelectedFile(null);
        setCurrentStepIndex(0);
    };

    return (
        <div className="seed-guide-container">
            <h2>AI Planting Guide 🍌 (Nanobanana Pro)</h2>

            {!steps.length && (
                <div className="upload-section">
                    <p>タネの写真をアップロードしてください。AIが植え方をガイドします。</p>
                    <input type="file" accept="image/*" onChange={handleFileChange} />
                    <button onClick={handleUpload} disabled={!selectedFile || loading}>
                        {loading ? 'AI分析中 (Gemini 3 + Image Gen)...' : 'ガイドを作成'}
                    </button>
                    {error && <p className="error-msg">{error}</p>}
                </div>
            )}

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

            {loading && (
                <div className="loading-overlay">
                    <div className="spinner"></div>
                    <p>AIが分析・画像生成中です...しばらくお待ちください。</p>
                </div>
            )}
        </div>
    );
}
