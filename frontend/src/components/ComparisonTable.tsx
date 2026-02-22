import { useState } from "react";
import { Loader2, CheckCircle, XCircle, ChevronDown, ChevronUp } from "lucide-react";
import clsx from "clsx";
import type { CompanyData, MetricRow } from "@/types/analysis";
import { METRIC_ROWS } from "@/types/analysis";

interface Props {
  companies: string[];
  data: Record<string, CompanyData>;
  onSelectCompany: (company: string) => void;
}

// ── Company metadata ────────────────────────────────────────────────────────

const COMPANY_META: Record<string, { flag: string }> = {
  "Lockheed Martin": { flag: "🇺🇸" },
  "RTX CORP":        { flag: "🇺🇸" },
  "BAE Systems":     { flag: "🇬🇧" },
  "BOEING CO":       { flag: "🇺🇸" },
  "SAAB AB":         { flag: "🇸🇪" },
};

// ── Filler placeholder data ─────────────────────────────────────────────────

const FILLER: Record<string, Record<string, number>> = {
  "Lockheed Martin": { transparency: 22, risk_mitigation: 17, safety: 29, cost: 14 },
  "RTX CORP":        { transparency: 35, risk_mitigation: 28, safety: 41, cost: 26 },
  "BAE Systems":     { transparency: 51, risk_mitigation: 49, safety: 47, cost: 43 },
  "BOEING CO":       { transparency: 31, risk_mitigation: 24, safety: 36, cost: 21 },
  "SAAB AB":         { transparency: 68, risk_mitigation: 63, safety: 71, cost: 55 },
};


type GradeInfo = { grade: string; textColor: string; bgColor: string };

function pctToGrade(pct: number): GradeInfo {
  if (pct >= 80) return { grade: "A", textColor: "text-green-400",  bgColor: "bg-green-500/15"  };
  if (pct >= 60) return { grade: "B", textColor: "text-lime-400",   bgColor: "bg-lime-500/15"   };
  if (pct >= 40) return { grade: "C", textColor: "text-amber-400",  bgColor: "bg-amber-500/15"  };
  if (pct >= 20) return { grade: "D", textColor: "text-orange-400", bgColor: "bg-orange-500/15" };
  return                { grade: "F", textColor: "text-red-400",    bgColor: "bg-red-500/15"    };
}

function companyAvgGrade(company: string): GradeInfo {
  const vals = Object.values(FILLER[company] ?? {});
  const avg = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
  return pctToGrade(avg);
}

// ── Helpers ─────────────────────────────────────────────────────────────────

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

// ── Cell renderer ────────────────────────────────────────────────────────────

function MetricCell({ metricKey, company, cd }: { metricKey: string; company: string; cd: CompanyData }) {
  if (cd.status === "error") {
    return (
      <td className="h-24 w-40 border-b border-r border-[#1f2937] px-4 py-6">
        <span className="text-xs text-red-400">{cd.error?.slice(0, 60) ?? "Error"}</span>
      </td>
    );
  }

  if (cd.status === "running" || cd.status === "ingesting") {
    return (
      <td className="h-24 w-40 border-b border-r border-[#1f2937] px-4 py-6">
        <div className="h-4 w-3/4 animate-pulse rounded bg-[#1f2937]" />
      </td>
    );
  }

  const pct = FILLER[company]?.[metricKey] ?? 0;
  const { grade, textColor, bgColor } = pctToGrade(pct);

  return (
    <td className={clsx("h-24 w-44 border-b border-r border-[#1f2937] text-center align-middle text-3xl font-bold", bgColor, textColor)}>
      {grade}
    </td>
  );
}

// ── Main component ───────────────────────────────────────────────────────────

export default function ComparisonTable({ companies, data, onSelectCompany }: Props) {
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
              const avg = companyAvgGrade(company);
              const meta = COMPANY_META[company];
              return (
                <th key={company} className="w-44 min-w-[176px] border-b border-r border-[#1f2937] px-4 py-5 align-top">
                  <div className="flex flex-col gap-2">
                    {/* Flag + name + grade */}
                    <div className="flex items-center gap-1.5">
                      <span className="text-base leading-none">{meta?.flag}</span>
                      <button
                        onClick={() => onSelectCompany(company)}
                        className="text-left text-base font-bold text-white leading-tight hover:text-red-400 transition-colors underline-offset-2 hover:underline"
                      >
                        {company}
                      </button>
                      <span className={clsx(
                        "shrink-0 rounded px-1.5 py-0.5 text-xs font-bold",
                        avg.bgColor, avg.textColor
                      )}>
                        {avg.grade}
                      </span>
                    </div>

                    {/* Agent status (when running) */}
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
                        company={company}
                        cd={data[company]}
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