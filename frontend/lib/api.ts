const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    if (res.status === 401 && getToken()) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/";
    }
    throw new Error(err.detail || "Request failed");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request<{ access_token: string; user_id: number; name: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<{ user_id: number; email: string; name: string; is_superuser: boolean; weekly_goal: number | null; monthly_goal: number | null }>("/api/auth/me"),

  // Activities
  createActivity: (data: object) =>
    request<ActivityResponse>("/api/activities", { method: "POST", body: JSON.stringify(data) }),
  listActivities: (params?: { start_date?: string; end_date?: string; user_id?: number }) => {
    const q = new URLSearchParams();
    if (params?.start_date) q.set("start_date", params.start_date);
    if (params?.end_date) q.set("end_date", params.end_date);
    if (params?.user_id) q.set("user_id", String(params.user_id));
    return request<ActivityResponse[]>(`/api/activities${q.toString() ? "?" + q : ""}`);
  },
  getActivity: (id: number) => request<ActivityResponse>(`/api/activities/${id}`),
  updateActivity: (id: number, data: object) =>
    request<ActivityResponse>(`/api/activities/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteActivity: (id: number) =>
    request<{ success: boolean }>(`/api/activities/${id}`, { method: "DELETE" }),

  // Leaderboards
  dailyLeaderboard: (date?: string) =>
    request<LeaderboardEntry[]>(`/api/leaderboards/daily${date ? `?date=${date}` : ""}`),
  weeklyLeaderboard: (weekStart?: string) =>
    request<LeaderboardEntry[]>(`/api/leaderboards/weekly${weekStart ? `?week_start=${weekStart}` : ""}`),
  monthlyLeaderboard: (year?: number, month?: number) => {
    const q = new URLSearchParams();
    if (year) q.set("year", String(year));
    if (month) q.set("month", String(month));
    return request<LeaderboardEntry[]>(`/api/leaderboards/monthly${q.toString() ? "?" + q : ""}`);
  },

  // Garmin
  garminStatus: () =>
    request<{ connected: boolean; email: string | null }>("/api/garmin/status"),
  garminConnect: (email: string, password: string) =>
    request<{ connected: boolean; email: string | null }>("/api/garmin/connect", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  garminSync: (start_date: string, end_date: string) =>
    request<{ imported: number; skipped: number; steps_updated: number; health_synced: number; warnings: string[] }>("/api/garmin/sync", {
      method: "POST",
      body: JSON.stringify({ start_date, end_date }),
    }),
  garminDisconnect: () =>
    request<{ success: boolean }>("/api/garmin/disconnect", { method: "DELETE" }),

  // Stats
  statsOverview: () =>
    request<{
      streaks: { user_id: number; name: string; streak: number }[];
      weekly_trend: { week_start: string; totals: Record<string, number> }[];
    }>("/api/stats/overview"),
  statsChallengeRecord: () =>
    request<ChallengeRecord>("/api/stats/challenge-record"),
  statsHealth: (days = 14) =>
    request<HealthTrends>(`/api/stats/health?days=${days}`),

  // Settings
  getConversionRules: () => request<ConversionRule[]>("/api/settings/conversion-rules"),
  createConversionRule: (data: { activity_type: string; conversion_per_minute: number; conversion_per_km: number }) =>
    request<ConversionRule>("/api/settings/conversion-rules", { method: "POST", body: JSON.stringify(data) }),
  updateConversionRule: (activityType: string, data: { conversion_per_minute?: number; conversion_per_km?: number }) =>
    request<{ success: boolean; message: string }>(`/api/settings/conversion-rules/${encodeURIComponent(activityType)}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  getUserSettings: () =>
    request<{ user_id: number; email: string; name: string; weekly_goal: number | null; monthly_goal: number | null }>("/api/settings/user"),
  updateUserSettings: (data: { name?: string; weekly_goal?: number | null; monthly_goal?: number | null }) =>
    request<{ success: boolean }>("/api/settings/user", { method: "PUT", body: JSON.stringify(data) }),
};

export interface ActivityResponse {
  id: number;
  user_id: number;
  activity_type: string;
  duration_minutes: number | null;
  distance_km: number | null;
  manual_steps: number | null;
  step_equivalent_calculated: number;
  date: string;
  notes: string | null;
  source: string;
  garmin_activity_id: string | null;
  created_at: string;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  name: string;
  total_steps: number;
  goal: number | null;
  goal_progress: number | null;
}

export interface HealthDataPoint {
  date: string;
  value: number;
}

export type HealthTrends = Record<string, HealthDataPoint[]>;

export interface ChallengeRecord {
  users: { user_id: number; name: string }[];
  weekly: {
    history: { period_start: string; winner_user_id: number | null; scores: Record<string, number> }[];
    wins: Record<string, number>;
    ties: number;
  };
  monthly: {
    history: { period_start: string; winner_user_id: number | null; scores: Record<string, number> }[];
    wins: Record<string, number>;
    ties: number;
  };
}

export interface ConversionRule {
  activity_type: string;
  conversion_per_minute: number;
  conversion_per_km: number;
}
