import {
  AlertTriangle,
  CheckCircle,
  Lightbulb,
  Network,
} from "lucide-react";
import React, { useState } from "react";

/* ---------------- ALERT CARD ---------------- */
const AlertCard = (props: any) => {
  const Icon = props.icon;

  return (
    <div
      className={`group ${props.bg} border ${props.border} rounded-xl p-6 ${props.hoverBg}`}
    >
      <div className="flex justify-between">
        <div className="flex gap-4">
          <div
            className={`w-12 h-12 rounded-lg ${props.iconBg} flex items-center justify-center border ${props.iconBorder}`}
          >
            <Icon className={`w-6 h-6 ${props.iconColor}`} />
          </div>

          <div>
            <div className="flex gap-2 mb-1">
              <span className={`text-xs font-bold ${props.badgeColor}`}>
                {props.badge}
              </span>
              <span className="text-[10px] text-gray-400">{props.id}</span>
            </div>

            <h4 className="text-lg font-bold">{props.title}</h4>
            <p className={`text-sm ${props.subtitleColor}`}>
              {props.subtitle}
            </p>
          </div>
        </div>

        <div className="text-right">
          <div className={`text-xl font-bold ${props.lagColor}`}>
            {props.lag}
          </div>
          <div className={`text-xs ${props.lagLabelColor}`}>
            {props.lagLabel}
          </div>
        </div>
      </div>
    </div>
  );
};

/* ---------------- ROADMAP PARSER (FINAL) ---------------- */
const cleanText = (text: string) => {
  return text
    .replace(/\*\*/g, "")
    .replace(/\*/g, "")
    .replace(/•/g, "")
    .replace(/^\d+\.\s*/, "")
    .trim();
};

const formatRoadmap = (text: string) => {
  if (!text) return [];

  const sections: any[] = [];

  const rawSections = text.includes("###")
    ? text.split("###").slice(1)
    : ["Overview\n" + text];

  rawSections.forEach((sec) => {
    const lines = sec.split("\n").map((l) => l.trim()).filter(Boolean);

    const title = cleanText(lines[0] || "Analysis");

    const points = lines
      .slice(1)
      .map((line) => cleanText(line))
      .filter((line) => line.length > 5);

    sections.push({
      title,
      points:
        points.length > 0
          ? points
          : [cleanText(sec)],
    });
  });

  return sections;
};

/* ---------------- PAGE ---------------- */
const BottlenecksPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("");



  const [form, setForm] = useState({
    title: "",
    abstract: "",
    year: 2020,
    cited: 5,
    novelty: 0.5,
    source: "IEEE",
  });

  const handleChange = (e: any) => {
    setForm({
      ...form,
      [e.target.name]:
        e.target.type === "number"
          ? Number(e.target.value)
          : e.target.value,
    });
  };

 const fetchAnalysis = async () => {
  setLoading(true);
  setLoadingMsg("Analyzing paper...");

  // After 4s, assume it might be a cold start and update the message
  const coldStartTimer = setTimeout(() => {
    setLoadingMsg("Model is waking up — this can take up to a minute on first request...");
  }, 4000);

  try {
    const res = await fetch(
      "http://localhost:8000/api/pipeline/analyze",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      }
    );

    const result = await res.json();
    setData(result);
  } catch (err) {
    console.error(err);
    setLoadingMsg("Something went wrong. Please try again.");
  } finally {
    clearTimeout(coldStartTimer);
    setLoading(false);
  }
};
  const roadmapSections = formatRoadmap(data?.roadmap);

  return (
    <main className="pt-24 px-12 pb-12 min-h-screen">
      {/* HEADER */}
      <header className="mb-10">
        <h1 className="text-4xl font-bold text-blue-400 mb-2">
          Innovation Bottleneck Detection
        </h1>
        <p className="text-gray-400">
          AI-driven research → patent conversion analysis
        </p>
      </header>

      {/* INPUT */}
      <div className="mb-10 bg-black/20 border p-6 rounded-xl">
        <h3 className="mb-4 font-bold">Research Input</h3>

        <div className="grid grid-cols-2 gap-4">
          <input name="title" placeholder="Title" onChange={handleChange} className="p-2 bg-black/30 rounded" />
          <input name="source" placeholder="Source" onChange={handleChange} className="p-2 bg-black/30 rounded" />

          <input name="year" type="number" placeholder="Year" onChange={handleChange} className="p-2 bg-black/30 rounded" />
          <input name="cited" type="number" placeholder="Citations" onChange={handleChange} className="p-2 bg-black/30 rounded" />

          <input name="novelty" type="number" step="0.1" placeholder="Novelty" onChange={handleChange} className="p-2 bg-black/30 rounded" />

          <textarea name="abstract" placeholder="Abstract" onChange={handleChange} className="col-span-2 p-2 bg-black/30 rounded" />
        </div>

        <button
          onClick={fetchAnalysis}
          disabled={loading}
          className={`
            mt-4 px-6 py-2.5 rounded-lg font-medium text-sm
            flex items-center gap-2
            transition-all duration-200
            ${loading
              ? "bg-blue-500/50 cursor-not-allowed text-blue-100"
              : "bg-blue-500 hover:bg-blue-400 active:scale-95 text-white shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30"
            }
          `}
        >
          {loading ? (
            <>
              <svg
                className="animate-spin h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                />
              </svg>
              <span>{loadingMsg || "Analyzing..."}</span>
            </>
          ) : (
            <span>Run Analysis</span>
          )}
        </button>
      </div>

      {/* GRID */}
      <div className="grid grid-cols-12 gap-8">
        {/* LEFT */}
        <div className="col-span-7 space-y-4">
          <AlertCard
            bg="bg-red-900/20"
            border="border-red-500/30"
            hoverBg="hover:bg-red-900/40"
            iconBg="bg-red-500/20"
            iconBorder="border-red-500/40"
            iconColor="text-red-400"
            icon={AlertTriangle}
            badgeColor="text-red-400"
            badge={data?.prediction?.label || "Awaiting"}
            id="AI-01"
            title={data?.paper?.title || "No Data"}
            subtitle={data?.prediction?.interpretation || ""}
            subtitleColor="text-red-200"
            lagColor="text-red-400"
            lag={
              data
                ? `${Math.round(data.prediction.probability * 100)}%`
                : "--"
            }
            lagLabel="Patent Probability"
            lagLabelColor="text-red-300"
          />

          <AlertCard
            bg="bg-green-900/20"
            border="border-green-500/30"
            hoverBg="hover:bg-green-900/40"
            iconBg="bg-green-500/20"
            iconBorder="border-green-500/40"
            iconColor="text-green-400"
            icon={CheckCircle}
            badgeColor="text-green-400"
            badge="System"
            id="SYS-01"
            title="ML Engine"
            subtitle="Pipeline Active"
            subtitleColor="text-green-200"
            lagColor="text-green-400"
            lag={loading ? "..." : "Active"}
            lagLabel="Status"
            lagLabelColor="text-green-300"
          />
        </div>

        {/* RIGHT - PROFESSIONAL ROADMAP */}
        <div className="col-span-5 space-y-4">
          <div className="p-6 border border-blue-500/20 rounded-xl bg-gradient-to-br from-black/40 to-black/10 backdrop-blur-xl shadow-lg">
            <Lightbulb className="mb-4 text-blue-400" />

            <h3 className="text-lg font-bold mb-4 text-blue-400">
              AI Strategic Roadmap
            </h3>

            {loading && (
              <p className="text-gray-400 animate-pulse">
                Generating structured insights...
              </p>
            )}

            {!loading && roadmapSections.length === 0 && (
              <p className="text-gray-500">
                Run analysis to generate roadmap
              </p>
            )}

            {!loading &&
              roadmapSections.map((sec: any, idx: number) => (
                <div key={idx} className="mb-6">
                  <h4 className="font-semibold text-blue-300 mb-2 border-l-2 border-blue-400 pl-2">
                    {sec.title}
                  </h4>

                  <ul className="space-y-2 text-sm text-gray-300">
                    {sec.points.map((p: string, i: number) => (
                      <li key={i} className="flex gap-2">
                        <span className="text-blue-400">•</span>
                        <span>{p}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <footer className="mt-12">
        <p>
          Confidence:{" "}
          <span className="font-bold">
            {data?.prediction?.confidence || "--"}
          </span>
        </p>
      </footer>

      {/* FAB */}
      <div className="fixed bottom-6 right-6">
        <button className="w-14 h-14 bg-black rounded-full flex items-center justify-center">
          <Network />
        </button>
      </div>
    </main>
  );
};

export default BottlenecksPage;