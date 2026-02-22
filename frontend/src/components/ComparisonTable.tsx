import { useState } from "react";
import { Loader2, CheckCircle, XCircle, ChevronDown, ChevronUp } from "lucide-react";
import clsx from "clsx";
import type { CompanyData, MetricRow, RankingResult, Grade } from "@/types/analysis";
import { METRIC_ROWS } from "@/types/analysis";

interface Props {
  companies: string[];
  data: Record<string, CompanyData>;
  rankings: Record<string, RankingResult>;
  onSelectCompany: (company: string) => void;
}

// ── Company metadata ────────────────────────────────────────────────────────

const COMPANY_META: Record<string, { flag: string }> = {
  "Lockheed Martin": { flag: "🇺🇸" },
  "RTX":             { flag: "🇺🇸" },
  "BAE Systems":     { flag: "🇬🇧" },
  "Boeing":          { flag: "🇺🇸" },
  "SAAB":            { flag: "🇸🇪" },
};

// ── Grade styling ────────────────────────────────────────────────────────────

type GradeInfo = { grade: string; textColor: string; bgColor: string };

function gradeToStyle(grade: Grade): GradeInfo {
  switch (grade) {
    case "A": return { grade, textColor: "text-green-400",  bgColor: "bg-green-500/15"  };
    case "B": return { grade, textColor: "text-lime-400",   bgColor: "bg-lime-500/15"   };
    case "C": return { grade, textColor: "text-amber-400",  bgColor: "bg-amber-500/15"  };
    case "D": return { grade, textColor: "text-orange-400", bgColor: "bg-orange-500/15" };
    case "E": return { grade, textColor: "text-red-300",    bgColor: "bg-red-500/10"    };
    case "F": return { grade, textColor: "text-red-400",    bgColor: "bg-red-500/15"    };
    default:  return { grade: "—", textColor: "text-gray-600", bgColor: "bg-[#1f2937]" };
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function AgentPip({ label, status }: { label: string; status: "idle" | "running" | "done" | "error" }) {
  return (
    <span className={clsx(
      "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium",
      status === "running" && "bg-amber-500/15 text-amber-300",
      status === "done"    && "bg-green-500/15 text-green-400",
      status === "error"   && "bg-red-500/15 text-red-400",
      status === "idle"    && "bg-[#1f2937] text-gray-600"
    )}>
      {status === "running" && <Loader2 className="h-2.5 w-2.5 animate-spin" />}
      {status === "done"    && <CheckCircle className="h-2.5 w-2.5" />}
      {status === "error"   && <XCircle className="h-2.5 w-2.5" />}
      {label}
    </span>
  );
}

// ── Cell renderer ─────────────────────────────────────────────────────────────

function MetricCell({
  metricKey,
  cd,
  ranking,
}: {
  metricKey: string;
  cd: CompanyData;
  ranking: RankingResult | undefined;
}) {
  if (cd.status === "error") {
    return (
      <td className="h-24 w-40 border-b border-r border-[#1f2937] px-4 py-6">
        <span className="text-xs text-red-400">{cd.error?.slice(0, 60) ?? "Error"}</span>
      </td>
    );
  }

  // Prefer live grade from streamed result stats, then fall back to pre-computed ranking
  const liveGrade = cd.result?.stats?.[`grade_${metricKey}`] as Grade | undefined;
  const rankingGrade = ranking?.grades?.[metricKey as keyof RankingResult["grades"]];
  const grade = (liveGrade || rankingGrade || null) as Grade | null;

  // Show skeleton only while running AND no grade data is available yet
  if ((cd.status === "running" || cd.status === "ingesting") && !grade) {
    return (
      <td className="h-24 w-40 border-b border-r border-[#1f2937] px-4 py-6">
        <div className="h-4 w-3/4 animate-pulse rounded bg-[#1f2937]" />
      </td>
    );
  }

  if (!grade || grade === "N/A") {
    return (
      <td className="h-24 w-44 border-b border-r border-[#1f2937] text-center align-middle">
        <span className="text-sm font-medium text-gray-600">N/A</span>
      </td>
    );
  }

  const { textColor, bgColor } = gradeToStyle(grade);
  return (
    <td className={clsx("h-24 w-44 border-b border-r border-[#1f2937] text-center align-middle text-3xl font-bold", bgColor, textColor)}>
      {grade}
    </td>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ComparisonTable({ companies, data, rankings, onSelectCompany }: Props) {
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({
    assessment: true,
  });

  const toggleCategory = (cat: string) =>
    setExpandedCategories((p) => ({ ...p, [cat]: !p[cat] }));

  const categories: Array<{ key: string; label: string; rows: MetricRow[] }> = [
    { key: "assessment", label: "Assessment", rows: METRIC_ROWS.filter((r) => r.category === "assessment") },
  ];

  return (
    <div className="overflow-x-auto rounded-xl border border-[#1f2937]">
      <table className="w-full border-collapse text-left">
        {/* ── Column headers ── */}
        <thead>
          <tr className="bg-[#111827]">
            <th className="sticky-col w-52 min-w-[200px] border-b border-r border-[#1f2937] bg-[#111827] px-5 py-4">
              <span className="text-[10px] font-semibold uppercase tracking-widest text-gray-600">
                Metric
              </span>
            </th>

            {companies.map((company) => {
              const cd = data[company];
              const ranking = rankings[company];

              // Overall grade: live result first, then pre-computed ranking
              const liveOverall = cd.result?.stats?.grade_overall as Grade | undefined;
              const overallGrade = (liveOverall || ranking?.overall || null) as Grade | null;
              const overall = overallGrade ? gradeToStyle(overallGrade) : null;

              return (
                <th key={company} className="w-44 min-w-[176px] border-b border-r border-[#1f2937] px-4 py-5 align-top">
                  <div className="flex flex-col items-center gap-2">
                    {/* Flag + name + overall grade */}
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => onSelectCompany(company)}
                        className="text-left text-base font-bold text-white leading-tight hover:text-red-400 transition-colors underline-offset-2 hover:underline"
                      >
                        {company}
                      </button>
                      {overall && (
                        <span className={clsx(
                          "shrink-0 rounded px-1.5 py-0.5 text-xs font-bold",
                          overall.bgColor, overall.textColor
                        )}>
                          {overall.grade}
                        </span>
                      )}
                    </div>

                    {/* Agent status pips */}
                    {cd.status === "running" && (
                      <div className="flex flex-wrap gap-1">
                        <AgentPip label="Investigator" status={cd.agentStatus.investigator} />
                        <AgentPip label="Forensic"     status={cd.agentStatus.forensic} />
                        <AgentPip label="Synthesizer"  status={cd.agentStatus.synthesizer} />
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
              {/* Category header */}
              <tr
                key={`cat-${cat.key}`}
                className="cursor-pointer select-none bg-[#0a0e1a] hover:bg-[#0d1220] transition-colors"
                onClick={() => toggleCategory(cat.key)}
              >
                <td colSpan={companies.length + 1} className="sticky-col border-b border-[#1f2937] bg-[#0a0e1a] px-5 py-2">
                  <div className="flex items-center gap-2">
                    {expandedCategories[cat.key]
                      ? <ChevronUp   className="h-3.5 w-3.5 text-gray-600" />
                      : <ChevronDown className="h-3.5 w-3.5 text-gray-600" />
                    }
                    <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                      {cat.label}
                    </span>
                  </div>
                </td>
              </tr>

              {/* Metric rows */}
              {expandedCategories[cat.key] &&
                cat.rows.map((metric) => (
                  <tr key={metric.key} className="group transition-colors hover:bg-[#111827]/60">
                    <td className="sticky-col border-b border-r border-[#1f2937] bg-[#0d1220] group-hover:bg-[#131c2e] px-5 py-4 align-top w-52 min-w-[200px]">
                      <p className="text-sm font-bold text-gray-200 leading-snug">{metric.label}</p>
                      <p className="mt-1 text-xs leading-snug text-gray-500">{metric.description}</p>
                    </td>

                    {companies.map((company) => (
                      <MetricCell
                        key={company}
                        metricKey={metric.key}
                        cd={data[company]}
                        ranking={rankings[company]}
                      />
                    ))}
                  </tr>
                ))}
            </>
          ))}
        </tbody>
      </table>
    </div>
  );
}
