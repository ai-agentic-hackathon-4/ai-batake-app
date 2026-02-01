"use client";

import { useEffect, useState, useRef } from "react";
import { Leaf, Plus, CloudUpload, Clock, X } from "lucide-react";
import styles from "./research.module.css";

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
    const [systemStatus, setSystemStatus] = useState<"idle" | "executing">("idle");
    const [uploading, setUploading] = useState(false);
    const [fileName, setFileName] = useState("Click to browse or drag file here");
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Poll for data
    useEffect(() => {
        fetchVegetables();
        const interval = setInterval(fetchVegetables, 5000);
        return () => clearInterval(interval);
    }, []);

    // Update system status based on vegetable status
    useEffect(() => {
        const isProcessing = vegetables.some((v) => v.status === "processing");
        setSystemStatus(isProcessing ? "executing" : "idle");
    }, [vegetables]);

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

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white font-sans relative overflow-x-hidden">
            {/* Background Gradients (inline styles for simplicity matching CSS) */}
            <div
                className="fixed inset-0 pointer-events-none"
                style={{
                    background: `
            radial-gradient(circle at 10% 20%, rgba(0, 255, 157, 0.1) 0%, transparent 20%),
            radial-gradient(circle at 90% 80%, rgba(0, 210, 255, 0.1) 0%, transparent 20%)
          `,
                }}
            />

            <header className={styles.header}>
                <div className={styles.logo}>
                    <Leaf className="w-6 h-6" />
                    AI Batake
                </div>
                <div className={`${styles.status_badge} ${systemStatus === "executing" ? styles.executing : ""}`}>
                    <div className={styles.status_dot}></div>
                    <span>{systemStatus === "executing" ? "Executing Deep Research..." : "System Idle"}</span>
                </div>
            </header>

            <main className={styles.main_content}>
                <div className={styles.section_header}>
                    <h1 className={styles.section_title}>Vegetable Research</h1>
                    <button className={styles.btn_primary} onClick={openModal}>
                        <Plus className="w-5 h-5" />
                        New Seed
                    </button>
                </div>

                <div className={styles.vegetable_grid}>
                    {vegetables.map((veg) => {
                        const isProcessing = veg.status === "processing";
                        let statusClass = "";
                        if (veg.status === "processing") statusClass = styles.status_processing;
                        if (veg.status === "completed") statusClass = styles.status_completed;
                        if (veg.status === "failed") statusClass = styles.status_failed;

                        return (
                            <div key={veg.id} className={styles.card} onClick={() => veg.status !== "processing" && setSelectedVeg(veg)}>
                                <div className={styles.card_header}>
                                    <div>
                                        <div className={styles.veg_name}>{veg.name}</div>
                                        <div className={styles.veg_id}>ID: {veg.id.substring(0, 8)}...</div>
                                    </div>
                                    <span className={`${styles.card_status} ${statusClass}`}>{veg.status}</span>
                                </div>
                                <div className="text-[#a0a0a0] text-sm flex gap-4 mb-4 items-center">
                                    <Clock className="w-4 h-4" />
                                    <span>{new Date(veg.created_at).toLocaleTimeString()}</span>
                                </div>
                                <div className={styles.progress_bar}>
                                    <div
                                        className={`${styles.progress_fill} ${isProcessing ? styles.processing : ""}`}
                                        style={{ width: isProcessing ? "60%" : "100%" }}
                                    ></div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </main>

            {/* Registration Modal */}
            {isModalOpen && (
                <div className={`${styles.modal_overlay} ${styles.active}`}>
                    <div className={`${styles.modal_content} ${styles.glass}`}>
                        <button className={styles.close_btn} onClick={closeModal}>
                            <X className="w-6 h-6" />
                        </button>
                        <h2 className={styles.section_title} style={{ marginBottom: "0.5rem", fontSize: "1.5rem" }}>
                            Register New Seed
                        </h2>
                        <p style={{ color: "#a0a0a0", marginBottom: "2rem" }}>
                            Upload an image of the seed packet to begin AI analysis.
                        </p>

                        <form onSubmit={handleSubmit}>
                            <div className={styles.form_group}>
                                <label className={styles.form_label}>Seed Packet Image</label>
                                <div
                                    className={styles.file_drop_zone}
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    <CloudUpload
                                        className="mx-auto mb-4 text-[#00ff9d]"
                                        size={48}
                                    />
                                    <p>{fileName}</p>
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        accept="image/*"
                                        style={{ display: "none" }}
                                        onChange={handleFileChange}
                                    />
                                </div>
                            </div>

                            <button type="submit" className={styles.btn_primary} style={{ width: "100%", justifyContent: "center" }} disabled={uploading}>
                                {uploading ? (
                                    <div className={styles.loader}></div>
                                ) : (
                                    <span>Register & Analyze</span>
                                )}
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* Detail Modal */}
            {selectedVeg && (
                <div className={`${styles.modal_overlay} ${styles.active}`}>
                    <div className={`${styles.modal_content} ${styles.glass}`} style={{ maxWidth: "800px" }}>
                        <button className={styles.close_btn} onClick={closeDetailModal}>
                            <X className="w-6 h-6" />
                        </button>
                        <h2 className={styles.section_title} style={{ marginBottom: "1.5rem", fontSize: "1.5rem" }}>
                            {selectedVeg.name}
                        </h2>
                        <div className={styles.detail_content}>
                            {selectedVeg.instructions ? (
                                <>
                                    {selectedVeg.instructions.volumetric_water_content && (
                                        <div className={styles.detail_item}>
                                            <div className={styles.detail_label}>Volumetric Water Content (%)</div>
                                            <div>{selectedVeg.instructions.volumetric_water_content}</div>
                                        </div>
                                    )}
                                    {Object.entries(selectedVeg.instructions).map(([key, value]) => {
                                        if (key === "original_analysis" || key === "name" || key === "volumetric_water_content") return null;
                                        return (
                                            <div key={key} className={styles.detail_item}>
                                                <div className={styles.detail_label}>{key.replace(/_/g, " ")}</div>
                                                <div>{String(value)}</div>
                                            </div>
                                        );
                                    })}
                                </>
                            ) : (
                                <p>No detailed data available.</p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
