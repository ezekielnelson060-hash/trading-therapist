function resolveApiBase(): string {
  const raw = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
  if (raw.endsWith("/api/v1")) return raw;
  return `${raw}/api/v1`;
}

const API_BASE = resolveApiBase();

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("tt_token");
}

export function setToken(token: string) {
  localStorage.setItem("tt_token", token);
}

export function clearToken() {
  localStorage.removeItem("tt_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(typeof err.detail === "string" ? err.detail : `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  register: (email: string, password: string, full_name?: string) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),
  login: async (email: string, password: string) => {
    const data = await request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(data.access_token);
    return data;
  },
  me: () => request<{ id: string; email: string; full_name: string; plan: string }>("/auth/me"),
  trades: (limit = 50) => request<any[]>(`/trades/?limit=${limit}`),
  summary: () =>
    request<{
      total_trades: number;
      total_pnl: number;
      avg_pnl: number;
      win_rate: number;
      wins: number;
      losses: number;
    }>("/trades/summary"),
  behavioral: () =>
    request<{
      total_trades_analyzed: number;
      recent_win_rate: number;
      events: any[];
      message: string;
    }>("/analytics/behavioral"),
  events: () => request<any[]>("/analytics/events"),
  acknowledgeEvent: (id: string) =>
    request(`/analytics/events/${id}/acknowledge`, { method: "POST" }),
  connectBroker: (broker: string, account_id?: string) =>
    request<{ id: string; api_token?: string; broker: string }>("/brokers/connect", {
      method: "POST",
      body: JSON.stringify({ broker, account_id }),
    }),
  brokers: () => request<any[]>("/brokers/"),
  chat: (message: string, session_id?: string) =>
    request<{
      session_id: string;
      reply: string;
      related_trade_count: number;
      related_events: string[];
      llm_used: boolean;
    }>("/chat/", {
      method: "POST",
      body: JSON.stringify({ message, session_id }),
    }),
  plans: () => request<any[]>("/plans/"),
  activePlan: () => request<any | null>("/plans/active"),
  createPlan: (body: any) =>
    request<any>("/plans/", { method: "POST", body: JSON.stringify(body) }),
  updatePlan: (id: string, body: any) =>
    request<any>(`/plans/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deletePlan: (id: string) => request(`/plans/${id}`, { method: "DELETE" }),
  uploadFlexCsv: async (file: File, account_id = "flex") => {
    const form = new FormData();
    form.append("file", file);
    form.append("account_id", account_id);
    return request<{
      status: string;
      parsed: number;
      created: number;
      skipped_duplicates: number;
      behavioral_events_created: number;
      warnings: string[];
      filename: string;
    }>("/connectors/ibkr/flex-upload", { method: "POST", body: form });
  },
};
