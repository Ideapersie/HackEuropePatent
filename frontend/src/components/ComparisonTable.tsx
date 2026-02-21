import { useState } from "react";
import { RefreshCw, Play, Loader2, CheckCircle, XCircle, ChevronDown, ChevronUp, Info } from "lucide-react";
import clsx from "clsx";
import type { CompanyData, MetricRow } from "@/types/analysis";
import { METRIC_ROWS } from "@/types/analysis";
import ContradictionModal from "./ContradictionModal";
import type { Contradiction } from "@/types/analysis";

interface Props {
  companies: string[];
  data: Record<string, CompanyData>;
  onIngest: (company: string) => void;
  onAnalyze: (company: string) => void;
}

// ── Helpers ────────────────────────────────────────────────────────────────

function riskColor(score: number): string {
  if (score >= 70) return "text-red-400";
  if (score >= 40) return "text-amber-400";
  return "text-green-400";
}

function cellBg(score: number | null): string {
  if (score === null) return "bg-[#0d1220]";
  if (score >= 70) return "bg-red-950/40 ring-1 ring-inset ring-red-900/40";
  if (score >= 40) return "bg-amber-950/40 ring-1 ring-inset ring-amber-900/40";
  return "bg-green-950/40 ring-1 ring-inset ring-green-900/40";
}

function AgentPip({
  label,
  status,
}: {
  label: string;
  status: "idle" | "running" | "done" | "error";
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium",
        status === "running" && "bg-amber-500/15 text-amber-300 agent-running",
        status === "done"    && "bg-green-500/15 text-green-400",
        status === "error"   && "bg-red-500/15 text-red-400",
        status === "idle"    && "bg-[#1f2937] text-gray-600"
      )}
    >
      {status === "running" && <Loader2 className="h-2.5 w-2.5 animate-spin" />}
      {status === "done"    && <CheckCircle className="h-2.5 w-2.5" />}
      {status === "error"   && <XCircle className="h-2.5 w-2.5" />}
      {label}
    </span>
  );
}

// ── Cell renderers per metric key ──────────────────────────────────────────

function MetricCell({
  metricKey,
  company,
  cd,
  onOpenContradiction,
}: {
  metricKey: string;
  company: string;
  cd: CompanyData;
  onOpenContradiction: (c: string, items: Contradiction[]) => void;
}) {
  const score = cd.result?.risk_score ?? null;
  const bg = cd.status === "done" ? cellBg(score) : "bg-[#0d1220]";

  if (cd.status === "error") {
    return (
      <td className="border-b border-r border-[#1f2937] px-4 py-3">
        <span className="text-xs text-red-400">{cd.error?.slice(0, 60) ?? "Error"}</span>
      </td>
    );
  }

  const loading = cd.status === "running" || cd.status === "ingesting";

  // ── Skeleton ──
  if (loading) {
    return (
      <td className="border-b border-r border-[#1f2937] px-4 py-3">
        <div className="h-4 w-3/4 animate-pulse rounded bg-[#1f2937]" />
      </td>
    );
  }

  // ── No data yet ──
  if (cd.status === "idle" || !cd.result) {
    return (
      <td className="border-b border-r border-[#1f2937] px-4 py-3">
        <span className="text-xs text-gray-700">—</span>
      </td>
    );
  }

  const result = cd.result;

  switch (metricKey) {
    case "patents_scanned":
      return (
        <td className={clsx("border-b border-r border-[#1f2937] px-4 py-3", bg)}>
          <span className="text-sm font-semibold text-blue-300">
            {result.stats?.patent ?? 0}
          </span>
        </td>
      );
    case "news_filings":
      return (
        <td className={clsx("border-b border-r border-[#1f2937] px-4 py-3", bg)}>
          <span className="text-sm font-semibold text-sky-300">
            {result.stats?.news ?? 0}
          </span>
        </td>
      );
    case "products_indexed":
      return (
        <td className={clsx("border-b border-r border-[#1f2937] px-4 py-3", bg)}>
          <span className="text-sm font-semibold text-purple-300">
            {result.stats?.product_image ?? 0}
          </span>
        </td>
      );
    case "risk_score":
      return (
        <td className={clsx("border-b border-r border-[#1f2937] px-4 py-3", bg)}>
          <div className="flex items-center gap-2">
            <span className={clsx("text-2xl font-black tabular-nums", riskColor(result.risk_score))}>
              {result.risk_score}
            </span>
            <span className="text-xs text-gray-600">/100</span>
            {/* Mini bar */}
            <div className="flex-1 min-w-[40px] h-1.5 rounded-full bg-[#1f2937]">
              <div
                className={clsx(
                  "h-full rounded-full transition-all duration-700",
                  result.risk_score >= 70 ? "bg-red-500" : result.risk_score >= 40 ? "bg-amber-400" : "bg-green-500"
                )}
                style={{ width: `${result.risk_score}%` }}
              />
            </div>
          </div>
        </td>
      );
    case "contradictions":
      return (
        <td className={clsx("border-b border-r border-[#1f2937] px-4 py-3", bg)}>
          <button
            onClick={() => onOpenContradiction(company, result.contradictions)}
            className="flex items-center gap-2 rounded hover:opacity-80 transition-opacity"
          >
            <span
              className={clsx(
                "flex h-7 w-7 items-center justify-center rounded-full text-sm font-bold",
                result.contradictions.length > 4
                  ? "bg-red-500/20 text-red-400"
                  : "bg-amber-500/20 text-amber-400"
              )}
            >
              {result.contradictions.length}
            </span>
            <span className="text-xs text-gray-500 underline underline-offset-2 decoration-dotted">
              view
            </span>
          </button>
        </td>
      );
    case "score_drivers":
      return (
        <td className={clsx("border-b border-r border-[#1f2937] px-4 py-4", bg)}>
          <ul className="space-y-1.5">
            {result.score_drivers.slice(0, 3).map((d, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                <span className="text-xs leading-snug text-gray-300">{d}</span>
              </li>
            ))}
          </ul>
        </td>
      );
    case "top_contradiction":
      const top = result.contradictions[0];
      if (!top) {
        return (
          <td className={clsx("border-b border-r border-[#1f2937] px-4 py-3", bg)}>
            <span className="text-xs text-gray-600">None identified</span>
          </td>
        );
      }
      return (
        <td className={clsx("border-b border-r border-[#1f2937] px-4 py-4 max-w-[260px]", bg)}>
          <p className="text-xs font-medium text-red-300 leading-snug line-clamp-2">
            &ldquo;{top.claim}&rdquo;
          </p>
          <p className="mt-1 text-[11px] text-gray-500 leading-snug line-clamp-2">
            {top.evidence}
          </p>
        </td>
      );
    default:
      return (
        <td className="border-b border-r border-[#1f2937] px-4 py-3">
          <span className="text-xs text-gray-700">—</span>
        </td>
      );
  }
}

// ── Main component ──────────────────────────────────────────────────────────

export default function ComparisonTable({ companies, data, onIngest, onAnalyze }: Props) {
  const [modal, setModal] = useState<{ company: string; items: Contradiction[] } | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({
    data: true,
    risk: true,
    findings: true,
  });

  const toggleCategory = (cat: string) =>
    setExpandedCategories((p) => ({ ...p, [cat]: !p[cat] }));

  // Group metric rows by category
  const categories: Array<{ key: string; label: string; rows: MetricRow[] }> = [
    { key: "data",     label: "Data Coverage",   rows: METRIC_ROWS.filter((r) => r.category === "data") },
    { key: "risk",     label: "Risk Assessment", rows: METRIC_ROWS.filter((r) => r.category === "risk") },
    { key: "findings", label: "Key Findings",    rows: METRIC_ROWS.filter((r) => r.category === "findings") },
  ];

  return (
    <>
      <div className="overflow-x-auto rounded-xl border border-[#1f2937]">
        <table className="w-full border-collapse text-left">
          {/* ── Column headers: companies ── */}
          <thead>
            {/* Company name row */}
            <tr className="bg-[#111827]">
              {/* Top-left corner: metric label column */}
              <th className="sticky-col w-52 min-w-[200px] border-b border-r border-[#1f2937] bg-[#111827] px-5 py-4">
                <span className="text-[10px] font-semibold uppercase tracking-widest text-gray-600">
                  Metric
                </span>
              </th>

              {companies.map((company) => {
                const cd = data[company];
                const busy = cd.status === "running" || cd.status === "ingesting";
                return (
                  <th
                    key={company}
                    className="min-w-[220px] border-b border-r border-[#1f2937] px-4 py-4 align-top"
                  >
                    <div className="flex flex-col gap-2">
                      {/* Company name */}
                      <span className="text-sm font-bold text-white leading-tight">{company}</span>

                      {/* Agent status pills (visible when running) */}
                      {cd.status === "running" && (
                        <div className="flex flex-wrap gap-1">
                          <AgentPip label="Investigator" status={cd.agentStatus.investigator} />
                          <AgentPip label="Forensic" status={cd.agentStatus.forensic} />
                          <AgentPip label="Synthesizer" status={cd.agentStatus.synthesizer} />
                        </div>
                      )}
                      {cd.status === "done" && (
                        <span className="text-[10px] text-green-500 flex items-center gap-1">
                          <CheckCircle className="h-3 w-3" /> Complete
                        </span>
                      )}
                      {cd.status === "error" && (
                        <span className="text-[10px] text-red-400 flex items-center gap-1">
                          <XCircle className="h-3 w-3" /> Failed
                        </span>
                      )}

                      {/* Action buttons */}
                      <div className="flex gap-1.5 pt-0.5">
                        <button
                          onClick={() => onIngest(company)}
                          disabled={busy}
                          title="Ingest data for this company"
                          className="flex items-center gap-1 rounded-md border border-[#374151] bg-[#1f2937] px-2 py-1 text-[10px] font-medium text-gray-400 transition hover:bg-[#374151] disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          <RefreshCw className={clsx("h-3 w-3", cd.status === "ingesting" && "animate-spin text-amber-400")} />
                          Ingest
                        </button>
                        <button
                          onClick={() => onAnalyze(company)}
                          disabled={busy}
                          title="Run AI analysis for this company"
                          className="flex items-center gap-1 rounded-md bg-red-700/80 px-2 py-1 text-[10px] font-medium text-red-100 transition hover:bg-red-600 disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          <Play className={clsx("h-3 w-3", cd.status === "running" && "animate-pulse")} />
                          Analyze
                        </button>
                      </div>
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>

          {/* ── Metric rows ── */}
          <tbody>
            {categories.map((cat) => (
              <>
                {/* Category header row */}
                <tr
                  key={`cat-${cat.key}`}
                  className="cursor-pointer select-none bg-[#0a0e1a] hover:bg-[#0d1220] transition-colors"
                  onClick={() => toggleCategory(cat.key)}
                >
                  <td
                    colSpan={companies.length + 1}
                    className="sticky-col border-b border-[#1f2937] bg-[#0a0e1a] px-5 py-2"
                  >
                    <div className="flex items-center gap-2">
                      {expandedCategories[cat.key]
                        ? <ChevronUp className="h-3.5 w-3.5 text-gray-600" />
                        : <ChevronDown className="h-3.5 w-3.5 text-gray-600" />
                      }
                      <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                        {cat.label}
                      </span>
                    </div>
                  </td>
                </tr>

                {/* Metric rows for this category */}
                {expandedCategories[cat.key] &&
                  cat.rows.map((metric) => (
                    <tr
                      key={metric.key}
                      className="group transition-colors hover:bg-[#111827]/60"
                    >
                      {/* Left sticky label column */}
                      <td className="sticky-col border-b border-r border-[#1f2937] bg-[#0d1220] group-hover:bg-[#131c2e] px-5 py-3 align-top w-52 min-w-[200px]">
                        <div className="flex items-start gap-1.5">
                          <div>
                            <p className="text-xs font-semibold text-gray-300 leading-snug">
                              {metric.label}
                            </p>
                            <p className="mt-0.5 text-[10px] leading-snug text-gray-600">
                              {metric.description}
                            </p>
                          </div>
                        </div>
                      </td>

                      {/* Per-company cells */}
                      {companies.map((company) => (
                        <MetricCell
                          key={company}
                          metricKey={metric.key}
                          company={company}
                          cd={data[company]}
                          onOpenContradiction={(c, items) => setModal({ company: c, items })}
                        />
                      ))}
                    </tr>
                  ))}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {/* Contradiction detail modal */}
      {modal && (
        <ContradictionModal
          company={modal.company}
          items={modal.items}
          onClose={() => setModal(null)}
        />
      )}
    </>
  );
}
