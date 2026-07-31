import React, { useState } from "react";

import { FileText, ShieldAlert, Sparkles, Upload } from "lucide-react";
import VerdictCard from "../components/PaperReview/VerdictCard";
import ScoreCard from "../components/PaperReview/ScoreCard";
import PlagiarismSignalsTable from "../components/PaperReview/PlagiarismSignalsTable";
import { reviewPaper, reviewOnly, plagiarismOnly, technicalReviewOnly } from "../services/paperReview";

const PaperReviewPage: React.FC = () => {

    const [file, setFile] =
        useState<File | null>(null);

    const [loading, setLoading] =
        useState(false);

    const [data, setData] =
        useState<any>(null);

    const [mode, setMode] = useState<
        "full" |
        "review" |
        "plagiarism" |
        "technical"
    >("full");

    const handleAnalyze = async () => {

        if (!file) return;

        try {

            setLoading(true);

            let result;

            if (mode === "full") {
                result =
                    await reviewPaper(file);
            }

            else if (
                mode === "review"
            ) {
                result =
                    await reviewOnly(file);
            }

            else if (
                mode === "plagiarism"
            ) {
                result =
                    await plagiarismOnly(
                        file
                    );
            }

            else {
                result =
                    await technicalReviewOnly(
                        file
                    );
            }

            setData(result);

        } catch (err) {

            console.error(err);

        } finally {

            setLoading(false);

        }
    };

    return (
        <main className="pt-24 px-10 pb-20 min-h-screen">

            {/* Header */}

            <div className="mb-12">

                <h1 className="text-5xl font-bold text-primary-container mb-2">
                    Research Paper Review & Integrity Analysis
                </h1>

                <p className="text-on-surface-variant">
                    AI-powered peer review and plagiarism detection
                </p>

            </div>

            <div className="grid md:grid-cols-4 gap-4 mb-6">

                <button
                    onClick={() =>
                        setMode("full")
                    }
                    className={`p-4 rounded-xl border transition-all ${mode === "full"
                        ? "border-primary bg-primary/10"
                        : "border-white/10"
                        }`}
                >
                    <p className="font-semibold">
                        Full Analysis
                    </p>

                    <p className="text-xs text-gray-400 mt-1">
                        Review + Plagiarism
                    </p>
                </button>

                <button
                    onClick={() =>
                        setMode("review")
                    }
                    className={`p-4 rounded-xl border transition-all ${mode === "review"
                        ? "border-primary bg-primary/10"
                        : "border-white/10"
                        }`}
                >
                    <p className="font-semibold">
                        Review Only
                    </p>

                    <p className="text-xs text-gray-400 mt-1">
                        Academic Peer Review
                    </p>
                </button>

                <button
                    onClick={() =>
                        setMode(
                            "plagiarism"
                        )
                    }
                    className={`p-4 rounded-xl border transition-all ${mode === "plagiarism"
                        ? "border-primary bg-primary/10"
                        : "border-white/10"
                        }`}
                >
                    <p className="font-semibold">
                        Plagiarism Only
                    </p>

                    <p className="text-xs text-gray-400 mt-1">
                        Originality Detection
                    </p>
                </button>

                <button
                    onClick={() => setMode("technical")}
                    className={`p-4 rounded-xl border transition-all ${mode === "technical"
                        ? "border-primary bg-primary/10"
                        : "border-white/10"
                        }`}
                >
                    <p className="font-semibold">
                        Technical Review
                    </p>

                    <p className="text-xs text-gray-400 mt-1">
                        Reviewer Comments
                    </p>
                </button>

            </div>

            {/* Upload Card */}

            <div className="glass-panel ghost-border rounded-3xl p-8 mb-10">

                {/* Header */}
                <div className="flex items-center gap-3 mb-6">
                    <div className="h-12 w-12 rounded-2xl bg-primary/10 flex items-center justify-center">
                        <FileText className="h-6 w-6 text-primary" />
                    </div>

                    <div>
                        <h2 className="text-2xl font-bold text-white">
                            Research Paper Analysis
                        </h2>

                        <p className="text-sm text-gray-400">
                            Upload your PDF to receive peer review, plagiarism analysis,
                            originality scoring, and publication readiness insights.
                        </p>
                    </div>
                </div>

                {/* Upload Area */}
                <label
                    htmlFor="paper-upload"
                    className="
      block
      border-2
      border-dashed
      border-[#ADC6FF33]
      rounded-2xl
      p-10
      text-center
      cursor-pointer
      transition-all
      hover:border-primary
      hover:bg-white/5
    "
                >
                    <div className="flex flex-col items-center gap-4">

                        <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                            <Upload className="h-8 w-8 text-primary" />
                        </div>

                        <div>
                            <h3 className="font-semibold text-lg text-white">
                                Drop your PDF here
                            </h3>

                            <p className="text-gray-400 text-sm mt-1">
                                or click to browse files
                            </p>
                        </div>

                        <p className="text-xs text-gray-500">
                            Supports PDF files up to 50MB
                        </p>

                        {file && (
                            <div className="mt-3 px-4 py-2 rounded-xl bg-primary/10 border border-primary/20">
                                <span className="text-primary text-sm font-medium">
                                    {file.name}
                                </span>
                            </div>
                        )}
                    </div>

                    <input
                        id="paper-upload"
                        type="file"
                        accept=".pdf"
                        className="hidden"
                        onChange={(e) =>
                            setFile(e.target.files?.[0] || null)
                        }
                    />
                </label>

                {/* Features */}
                <div className="grid md:grid-cols-4 gap-4 mt-6">

                    <div className="rounded-xl bg-[#111827] p-4 border border-white/5">
                        <p className="font-medium text-white">
                            Peer Review
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                            Academic quality evaluation across 8 dimensions.
                        </p>
                    </div>

                    <div className="rounded-xl bg-[#111827] p-4 border border-white/5">
                        <p className="font-medium text-white">
                            Plagiarism Detection
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                            AI-powered originality and reuse analysis.
                        </p>
                    </div>

                    <div className="rounded-xl bg-[#111827] p-4 border border-white/5">
                        <p className="font-medium text-white">
                            Publication Readiness
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                            Accept / Reject recommendation with rationale.
                        </p>
                    </div>

                    <div className="rounded-xl bg-[#111827] p-4 border border-white/5">
                        <p className="font-medium text-white">
                            Technical Review
                        </p>

                        <p className="text-xs text-gray-400 mt-1">
                            Detailed reviewer comments with actionable improvements.
                        </p>
                    </div>

                </div>

                {/* Action Button */}
                <button
                    onClick={handleAnalyze}
                    disabled={!file || loading}
                    className="
      mt-8
      w-full
      flex
      items-center
      justify-center
      gap-2
      py-4
      rounded-2xl
      bg-primary
      text-black
      font-semibold
      transition-all
      hover:scale-[1.01]
      disabled:opacity-50
      disabled:cursor-not-allowed
    "
                >
                    {loading ? (
                        <>
                            <div className="h-5 w-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                            Analyzing Paper...
                        </>
                    ) : (
                        <>
                            <Sparkles className="h-5 w-5" />
                            {
                                mode === "full"
                                    ? "Run Full Analysis"
                                    : mode === "review"
                                        ? "Run Peer Review"
                                        : mode === "plagiarism"
                                            ? "Run Plagiarism Check"
                                            : "Run Technical Review"
                            }
                        </>
                    )}
                </button>
            </div>

            {(data && !data?.technical_review) && (
                <>
                    {/* Top Grid */}

                    <div className="grid grid-cols-12 gap-8">

                        {/* LEFT */}

                        <div className="col-span-7 space-y-4">

                            {data?.peer_review && (
                                <>
                                    <VerdictCard
                                        verdict={
                                            data.peer_review
                                                .overall_verdict
                                        }
                                        score={
                                            data.peer_review
                                                .overall_score
                                        }
                                        confidence={
                                            data.peer_review
                                                .confidence
                                        }
                                    />
                                </>
                            )}

                            {data?.plagiarism_analysis && (
                                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6">

                                    <div className="flex justify-between">

                                        <div className="flex gap-3">

                                            <ShieldAlert className="text-red-400" />

                                            <div>

                                                <h3 className="font-bold">
                                                    Plagiarism Risk
                                                </h3>

                                                <p>
                                                    {
                                                        data
                                                            .plagiarism_analysis
                                                            .plagiarism_likelihood
                                                    }
                                                </p>

                                            </div>

                                        </div>

                                        <div className="text-3xl font-bold text-red-400">
                                            {
                                                data
                                                    .plagiarism_analysis
                                                    .estimated_plagiarism_percentage
                                            }%
                                        </div>

                                    </div>

                                </div>
                            )}
                        </div>

                        {/* RIGHT */}

                        <div className="col-span-5">

                            <div className="bg-gradient-to-br from-black/40 to-black/10 border border-primary/20 rounded-xl p-6">

                                <Sparkles className="text-primary mb-3" />

                                <h3 className="font-bold text-xl mb-4">
                                    Review Summary
                                </h3>

                                <p className="text-sm text-on-surface-variant">
                                    {data?.peer_review?.summary}
                                </p>

                            </div>

                        </div>

                    </div>

                    {/* Score Cards */}

                    <div className="grid grid-cols-4 gap-4 mt-10">
                        {data?.peer_review?.scores &&
                            Object.entries(
                                data.peer_review.scores
                            )?.map(([k, v]) => (
                                <ScoreCard
                                    key={k}
                                    label={k}
                                    value={v as number}
                                />
                            ))
                        }

                    </div>

                    {/* Strengths & Weaknesses */}
                    {data?.peer_review && (
                        <div className="grid grid-cols-2 gap-8 mt-10">

                            <div className="bg-surface-container p-6 rounded-xl ghost-border">

                                <h3 className="font-bold text-green-400 mb-4">
                                    Strengths
                                </h3>

                                <ul className="space-y-2">
                                    {data?.peer_review.strengths?.map(
                                        (s: string, i: number) => (
                                            <li key={i}>
                                                • {s}
                                            </li>
                                        )
                                    )}
                                </ul>

                            </div>

                            <div className="bg-surface-container p-6 rounded-xl ghost-border">

                                <h3 className="font-bold text-red-400 mb-4">
                                    Weaknesses
                                </h3>

                                <ul className="space-y-2">
                                    {data.peer_review.weaknesses?.map(
                                        (s: string, i: number) => (
                                            <li key={i}>
                                                • {s}
                                            </li>
                                        )
                                    )}
                                </ul>

                            </div>

                        </div>
                    )}

                    {/* Plagiarism Table */}

                    {data?.plagiarism_analysis && (
                        <PlagiarismSignalsTable
                            signals={
                                data
                                    .plagiarism_analysis
                                    ?.signals_found || []
                            }
                        />
                    )}

                    {/* Detailed Review */}

                    {data?.peer_review && (
                        <div className="mt-10 bg-surface-container rounded-2xl p-8 ghost-border">

                            <div className="flex items-center gap-3 mb-4">
                                <FileText />
                                <h3 className="font-bold text-xl">
                                    Detailed Review
                                </h3>
                            </div>

                            <p className="leading-relaxed whitespace-pre-wrap text-on-surface-variant">
                                {
                                    data.peer_review
                                        .detailed_review
                                }
                            </p>

                        </div>
                    )}
                </>
            )}

            {data?.technical_review?.review_comments && (

                <div className="mt-10 bg-surface-container rounded-2xl p-8 ghost-border">

                    <div className="flex items-center gap-3 mb-6">

                        <FileText className="text-primary" />

                        <h3 className="font-bold text-2xl">
                            Reviewer Comments
                        </h3>

                    </div>

                    <div className="space-y-5">

                        {data.technical_review.review_comments.map(
                            (item: any) => (

                                <div
                                    key={item.id}
                                    className="rounded-xl border border-white/10 p-5 bg-black/20"
                                >

                                    <div className="flex justify-between items-center mb-3">

                                        <span className="font-semibold text-primary">
                                            {item.category}
                                        </span>

                                        <span
                                            className={`px-3 py-1 rounded-full text-xs font-semibold
                                ${item.severity === "Critical"
                                                    ? "bg-red-500/20 text-red-400"
                                                    : item.severity === "Major"
                                                        ? "bg-yellow-500/20 text-yellow-300"
                                                        : "bg-blue-500/20 text-blue-300"
                                                }`}
                                        >
                                            {item.severity}
                                        </span>

                                    </div>

                                    <p className="text-gray-300 leading-7">
                                        {item.comment}
                                    </p>

                                    <div className="mt-4 p-4 rounded-lg bg-primary/10 border border-primary/20">

                                        <p className="text-primary font-medium mb-1">
                                            Recommendation
                                        </p>

                                        <p className="text-sm text-gray-300">
                                            {item.recommendation}
                                        </p>

                                    </div>

                                </div>
                            )
                        )}

                    </div>

                </div>

            )}
        </main>
    );
};

export default PaperReviewPage;