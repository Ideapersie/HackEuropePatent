import { useState, useCallback, useEffect } from "react";
import { Shield } from "lucide-react";
import { streamAnalysis, triggerIngest, fetchStats, fetchRankings } from "@/lib/api";
import type { CompanyData, AgentStatus, RankingResult } from "@/types/analysis";
import { emptyCompanyData } from "@/types/analysis";
import ComparisonTable from "@/components/ComparisonTable";
import CompanyPage from "@/components/CompanyPage";

// Fixed set of 5 companies shown as columns — must match keys in ranked_results.json
const COMPANIES = [
  "Lockheed Martin",
  "RTX",
  "BAE Systems",
  "Boeing",
  "SAAB",
];

type CompanyMap = Record<string, CompanyData>;

function initState(): CompanyMap {
  return Object.fromEntries(COMPANIES.map((c) => [c, emptyCompanyData()]));
}

export default function App() {
  const [data, setData] = useState<CompanyMap>(initState);
  const [globalBusy, setGlobalBusy] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [rankings, setRankings] = useState<Record<string, RankingResult>>({});

  useEffect(() => {
    fetchRankings().then(setRankings).catch(() => {});
  }, []);

  const patch = useCallback(
    (company: string, update: Partial<CompanyData>) =>
      setData((prev) => ({
        ...prev,
        [company]: { ...prev[company], ...update },
      })),
    []
  );

  const runCompany = useCallback(
    async (company: string) => {
      patch(company, {
        status: "running",
        error: null,
        result: null,
        agentStatus: { investigator: "running", forensic: "idle", synthesizer: "idle" },
      });

      try {
        const gen = streamAnalysis(company);
        for await (const event of gen) {
          if (event.node === "investigator") {
            patch(company, {
              agentStatus: { investigator: "done", forensic: "running", synthesizer: "idle" },
            });
          } else if (event.node === "forensic") {
            patch(company, {
              agentStatus: { investigator: "done", forensic: "done", synthesizer: "running" },
            });
          } else if (event.node === "synthesizer" || event.node === "complete") {
            const agentStatus: AgentStatus = {
              investigator: "done",
              forensic: "done",
              synthesizer: "done",
            };
            setData((prev) => ({
              ...prev,
              [company]: {
                ...prev[company],
                agentStatus,
                status: "done",
                result: event.data
                  ? { ...(prev[company].result ?? {}), ...event.data } as any
                  : prev[company].result,
              },
            }));
          } else if (event.node === "error") {
            patch(company, {
              status: "error",
              error: event.message ?? "Unknown error",
              agentStatus: { investigator: "idle", forensic: "idle", synthesizer: "idle" },
            });
          }
        }
      } catch (e: unknown) {
        patch(company, {
          status: "error",
          error: e instanceof Error ? e.message : "Analysis failed",
          agentStatus: { investigator: "idle", forensic: "idle", synthesizer: "idle" },
        });
      }
    },
    [patch]
  );

  const handleIngestOne = useCallback(
    async (company: string) => {
      patch(company, { status: "ingesting", error: null });
      try {
        await triggerIngest(company);
        const stats = await fetchStats(company);
        setData((prev) => ({
          ...prev,
          [company]: {
            ...prev[company],
            status: "idle",
            result: prev[company].result
              ? { ...prev[company].result!, stats }
              : null,
          },
        }));
      } catch (e: unknown) {
        patch(company, {
          status: "error",
          error: e instanceof Error ? e.message : "Ingestion failed",
        });
      }
    },
    [patch]
  );

  const handleAnalyzeOne = useCallback(
    (company: string) => runCompany(company),
    [runCompany]
  );

  const handleAnalyzeAll = useCallback(async () => {
    setGlobalBusy(true);
    // Run in parallel
    await Promise.allSettled(COMPANIES.map((c) => runCompany(c)));
    setGlobalBusy(false);
  }, [runCompany]);

  const anyRunning = COMPANIES.some(
    (c) => data[c].status === "running" || data[c].status === "ingesting"
  );

  // ── Company detail page ──
  if (selectedCompany) {
    return (
      <CompanyPage
        company={selectedCompany}
        cd={data[selectedCompany]}
        onBack={() => setSelectedCompany(null)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0e1a] flex flex-col">
      {/* ── Navbar ── */}
      <header className="sticky top-0 z-40 border-b border-[#1f2937] bg-[#111827]/95 backdrop-blur-sm">
        <div className="flex items-center justify-between gap-6 px-6 py-3">
          <div className="flex items-center gap-2.5">
            <Shield className="h-5 w-5  text-red-500" />
            <span className="font-bold tracking-tight text-white">PatentWatch</span>
            <span className="rounded bg-red-500/20 px-2 py-0.5 text-[10px] font-semibold text-red-400 uppercase tracking-wider">
              Beta
            </span>
          </div>

          <p className="hidden md:block text-xs text-gray-500 max-w-md text-center">
            AI-powered comparison of defense company public claims vs. EPO patent filings
          </p>

          <div />
        </div>
      </header>

      {/* ── Legend ── */}
      <div className="flex items-center gap-6 border-b border-[#1f2937] bg-[#0d1220] px-6 py-2">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-gray-600">
          Legend
        </span>
        {[
          { color: "bg-[#1f2937]", label: "No data" },
          { color: "bg-green-900/50 ring-1 ring-green-700/40", label: "Low risk (0–39)" },
          { color: "bg-amber-900/50 ring-1 ring-amber-700/40", label: "Moderate (40–69)" },
          { color: "bg-red-900/50 ring-1 ring-red-700/40", label: "High risk (70+)" },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className={`h-3 w-3 rounded-sm ${color}`} />
            <span className="text-[11px] text-gray-500">{label}</span>
          </div>
        ))}
      </div>

      {/* ── Intro ── */}
      <div className="px-24 pt-10 pb-4">
        <h1 className="flex items-center text-6xl font-black tracking-tight text-white">
          Patent<span className="text-red-500">Watch</span>
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-gray-400">
          We make defence AI understandable by turning technical documents into clear safety signals
          for everyone. Our goal is to give the public and policymakers a simple, independent view
          of where AI may be risky.
        </p>
      </div>

      {/* ── Main table ── */}
      <main className="flex-1 overflow-x-auto px-24 py-6">
        <ComparisonTable
          companies={COMPANIES}
          data={data}
          rankings={rankings}
          onSelectCompany={setSelectedCompany}
        />
      </main>

      <footer className="border-t border-[#1f2937] px-6 py-3 text-center text-[11px] text-gray-600">
        Data sourced from EPO OPS API · yfinance · Public company websites · Powered by Gemini 1.5 Pro + LangGraph
      </footer>
    </div>
  );
}
