export interface Contradiction {
  claim: string;
  evidence: string;
  why_it_matters: string;
  sources: string[];
}

export interface AnalysisResult {
  risk_score: number;
  score_drivers: string[];
  products: string[];
  contradictions: Contradiction[];
  stats: Record<string, number>;
  investigator_status: "pending" | "running" | "done" | "error";
  forensic_status: "pending" | "running" | "done" | "error";
  synthesizer_status: "pending" | "running" | "done" | "error";
}

export interface AgentStreamEvent {
  node: "investigator" | "forensic" | "synthesizer" | "complete" | "error";
  status: string;
  data?: Partial<AnalysisResult>;
  message?: string;
}

export interface AgentStatus {
  investigator: "idle" | "running" | "done" | "error";
  forensic: "idle" | "running" | "done" | "error";
  synthesizer: "idle" | "running" | "done" | "error";
}

// ── Multi-company matrix state ──────────────────────────────────────────────

export type CompanyStatus = "idle" | "ingesting" | "running" | "done" | "error";

export interface CompanyData {
  status: CompanyStatus;
  agentStatus: AgentStatus;
  result: AnalysisResult | null;
  error: string | null;
}

export function emptyCompanyData(): CompanyData {
  return {
    status: "idle",
    agentStatus: { investigator: "idle", forensic: "idle", synthesizer: "idle" },
    result: null,
    error: null,
  };
}

// ── Rankings (from GET /api/rankings) ────────────────────────────────────────

export type Grade = "A" | "B" | "C" | "D" | "E" | "F" | "N/A";

export interface RankingResult {
  company: string;
  grades: {
    contradiction: Grade;
    risk_mitigation: Grade;
    safety: Grade;
    cost: Grade;
  };
  overall: Grade;
  overall_score: number;
  aggregated_scores: {
    contradiction_pct: number;
    risk_mitigation: number;
    risk_score: number;
    avg_unit_cost_usd: number | null;
  };
  product_count: number;
}

// ── Metric rows ──────────────────────────────────────────────────────────────

export interface MetricRow {
  key: string;
  label: string;
  description: string;
  category: "assessment";
}

export const METRIC_ROWS: MetricRow[] = [
  { key: "contradiction",   label: "Transparency",    description: "% of public claims contradicted by patent evidence",                        category: "assessment" },
  { key: "risk_mitigation", label: "Risk Mitigation", description: "Human-in-the-loop safeguards in autonomous and AI-guided systems",           category: "assessment" },
  { key: "safety",          label: "Safety",          description: "Adherence to civilian safety standards and international humanitarian law",   category: "assessment" },
  { key: "cost",            label: "Cost",            description: "Average unit cost of products (higher cost = worse score)",                   category: "assessment" },
];
