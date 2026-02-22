import type { AnalysisResult, AgentStreamEvent, RankingResult } from "@/types/analysis";

// Vite exposes env vars via import.meta.env
const BASE = (import.meta.env.VITE_API_URL as string | undefined) || "http://localhost:8000";

export async function fetchCompanies(): Promise<string[]> {
  const res = await fetch(`${BASE}/api/companies`);
  if (!res.ok) throw new Error("Failed to fetch companies");
  const data = await res.json();
  return data.companies as string[];
}

export async function fetchStats(company: string): Promise<Record<string, number>> {
  const res = await fetch(`${BASE}/api/stats/${encodeURIComponent(company)}`);
  if (!res.ok) return {};
  const data = await res.json();
  return data.stats as Record<string, number>;
}

export async function triggerIngest(company: string): Promise<void> {
  const res = await fetch(`${BASE}/api/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ company_name: company }),
  });
  if (!res.ok) throw new Error("Ingestion failed");
}

export async function runAnalysis(
  company: string,
  query: string = ""
): Promise<AnalysisResult> {
  const res = await fetch(`${BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ company_name: company, user_query: query }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || "Analysis failed");
  }
  return res.json() as Promise<AnalysisResult>;
}

export async function fetchRankings(): Promise<Record<string, RankingResult>> {
  const res = await fetch("/ranked_results.json");
  if (!res.ok) return {};
  const data = await res.json();
  return Object.fromEntries(
    (data.rankings as RankingResult[]).map((r) => [r.company, r])
  );
}

export async function* streamAnalysis(
  company: string,
  query: string = ""
): AsyncGenerator<AgentStreamEvent> {
  const res = await fetch(`${BASE}/api/analyze/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ company_name: company, user_query: query }),
  });

  if (!res.ok || !res.body) throw new Error("Stream failed");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      const dataLine = line.replace(/^data:\s*/, "").trim();
      if (!dataLine) continue;
      try {
        yield JSON.parse(dataLine) as AgentStreamEvent;
      } catch {
        // skip malformed SSE frames
      }
    }
  }
}
