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
    request("/auth/register", { method: "POST", body: JSON.stringify({ email, password, full_name }) }),
  login: async (email: string, password: string) => {
    const data = await request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(data.access_token);
    return data;
  },
  me: () => request<any>("/auth/me"),
  trades: (limit = 50) => request<any[]>(`/trades/?limit=${limit}`),
  tradesWithContext: (limit = 40) =>
    request<{ trades: any[]; count: number }>(`/trades/with-context?limit=${limit}`),
  summary: () => request<any>("/trades/summary"),
  tilt: () => request<any>("/analytics/tilt"),
  behavioral: () => request<any>("/analytics/behavioral"),
  events: () => request<any[]>("/analytics/events"),
  weekly: () => request<any>("/analytics/weekly"),
  acknowledgeEvent: (id: string) => request(`/analytics/events/${id}/acknowledge`, { method: "POST" }),
  acknowledgePause: () => request<any>("/analytics/pause/acknowledge", { method: "POST" }),
  overridePause: () => request<any>("/analytics/pause/override", { method: "POST" }),
  connectBroker: (broker: string, account_id?: string) =>
    request<any>("/brokers/connect", { method: "POST", body: JSON.stringify({ broker, account_id }) }),
  brokers: () => request<any[]>("/brokers/"),
  chat: (message: string, session_id?: string) =>
    request<any>("/chat/", { method: "POST", body: JSON.stringify({ message, session_id }) }),
  plans: () => request<any[]>("/plans/"),
  activePlan: () => request<any | null>("/plans/active"),
  createPlan: (body: any) => request<any>("/plans/", { method: "POST", body: JSON.stringify(body) }),
  updatePlan: (id: string, body: any) => request<any>(`/plans/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deletePlan: (id: string) => request(`/plans/${id}`, { method: "DELETE" }),
  createCheckIn: (body: any) => request<any>("/checkins/", { method: "POST", body: JSON.stringify(body) }),
  motiveStats: () => request<any>("/checkins/motives/stats"),
  demoSeed: () => request<any>("/trades/demo-seed", { method: "POST" }),
  alerts: () => request<any[]>("/alerts/"),
  evaluateAlerts: () => request<any>("/alerts/evaluate", { method: "POST" }),
  markAlertRead: (id: string) => request(`/alerts/${id}/read`, { method: "POST" }),
  lockStatus: () => request<any>("/lock/"),
  engageLock: (minutes = 60) =>
    request<any>("/lock/engage", { method: "POST", body: JSON.stringify({ minutes }) }),
  autoLock: () => request<any>("/lock/auto-from-tilt", { method: "POST" }),
  releaseLock: () => request<any>("/lock/release", { method: "POST" }),
  billingPlans: () => request<any>("/billing/plans"),
  billingMe: () => request<any>("/billing/me"),
  checkout: (plan: string) => request<any>(`/billing/checkout?plan=${encodeURIComponent(plan)}`, { method: "POST" }),
  teams: () => request<any[]>("/teams/"),
  createTeam: (name: string) => request<any>("/teams/", { method: "POST", body: JSON.stringify({ name }) }),
  inviteTeam: (teamId: string, email: string) =>
    request<any>(`/teams/${teamId}/invite`, { method: "POST", body: JSON.stringify({ email, role: "trader" }) }),
  teamRisk: (teamId: string) => request<any>(`/teams/${teamId}/risk`),
  onboardingStatus: () => request<any>("/onboarding/status"),
  saveOnboarding: (body: any) =>
    request<any>("/onboarding/profile", { method: "POST", body: JSON.stringify(body) }),
  uploadFlexCsv: async (file: File, account_id = "flex") => {
    const form = new FormData();
    form.append("file", file);
    form.append("account_id", account_id);
    return request<any>("/connectors/ibkr/flex-upload", { method: "POST", body: form });
  },
};
