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

// ── Metric rows ──────────────────────────────────────────────────────────────

export interface MetricRow {
  key: string;
  label: string;
  description: string;
  category: "data" | "risk" | "findings";
}

export const METRIC_ROWS: MetricRow[] = [
  // Data coverage
  { key: "patents_scanned",   label: "Patents scanned",   description: "EPO patent records ingested into the vector store",          category: "data" },
  { key: "news_filings",      label: "News filings",      description: "Press releases & news items fetched via yfinance",           category: "data" },
  { key: "products_indexed",  label: "Products indexed",  description: "Product images scraped & embedded via Gemini multimodal",    category: "data" },
  // Risk assessment
  { key: "risk_score",        label: "Risk score",        description: "0–100 transparency risk from the AI Synthesizer agent",      category: "risk" },
  { key: "contradictions",    label: "Contradictions",    description: "Claim-vs-patent discrepancies identified by the AI",         category: "risk" },
  // Findings
  { key: "score_drivers",     label: "Score drivers",     description: "Key reasons behind the risk score (top 3 bullets)",         category: "findings" },
  { key: "top_contradiction", label: "Top finding",       description: "Most significant discrepancy between public claims & patents", category: "findings" },
];
