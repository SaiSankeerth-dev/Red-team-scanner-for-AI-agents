export const API_BASE =
  process.env.NEXT_PUBLIC_REDLINE_API ?? "http://localhost:8000";

export interface CampaignSummary {
  id: number;
  name: string;
  target: string;
  pack: string;
  created_at: string;
  verdict_counts: Record<string, number>;
}

export interface ProbeRow {
  name: string;
  severity: string;
  description: string;
  total: number;
  fail: number;
  partial: number;
  pass: number;
  status: string;
}

export interface Finding {
  probe_name: string;
  severity: string;
  messages: { role: string; content: string }[];
  response: string;
  notes: string;
  remediation: string;
}

export interface ReportSummary {
  campaign: {
    id: number;
    name: string;
    target: string;
    pack: string;
    created_at: string;
  };
  generated_at: string;
  score: number;
  grade: string;
  counts: { fail: number; partial: number; pass: number; total: number };
  probes: ProbeRow[];
  findings: Finding[];
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status}: ${detail.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  campaigns: () => req<CampaignSummary[]>("/campaigns"),
  summary: (id: number | string) => req<ReportSummary>(`/campaigns/${id}/summary`),
  reportUrl: (id: number | string) => `${API_BASE}/campaigns/${id}/report`,
  pdfUrl: (id: number | string) => `${API_BASE}/campaigns/${id}/report?format=pdf`,
  createCampaign: (body: {
    target?: string;
    pack?: string;
    name?: string;
    adapter?: string;
    adapter_config?: Record<string, unknown>;
  }) => req<{ id: number }>(`/campaigns`, { method: "POST", body: JSON.stringify(body) }),
};

export function gradeClass(grade: string): string {
  return `grade grade-${grade}`;
}
