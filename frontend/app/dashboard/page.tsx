"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, LeaderboardEntry, ActivityResponse } from "@/lib/api";
import Nav from "@/components/Nav";
import LeaderboardTable from "@/components/LeaderboardTable";
import TrendChart from "@/components/TrendChart";

type Period = "daily" | "weekly" | "monthly";

interface StatsOverview {
  streaks: { user_id: number; name: string; streak: number }[];
  weekly_trend: { week_start: string; totals: Record<string, number> }[];
}

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [period, setPeriod] = useState<Period>("weekly");
  const [data, setData] = useState<LeaderboardEntry[]>([]);
  const [fetching, setFetching] = useState(true);
  const [stats, setStats] = useState<StatsOverview | null>(null);
  const [opponentActivities, setOpponentActivities] = useState<ActivityResponse[]>([]);
  const opponentFetched = useRef(false);

  useEffect(() => {
    if (!loading && !user) router.replace("/");
  }, [user, loading, router]);

  const fetchLeaderboard = useCallback(async () => {
    setFetching(true);
    try {
      let result: LeaderboardEntry[];
      if (period === "daily") result = await api.dailyLeaderboard();
      else if (period === "weekly") result = await api.weeklyLeaderboard();
      else result = await api.monthlyLeaderboard();
      setData(result);
    } catch {
      //
    } finally {
      setFetching(false);
    }
  }, [period]);

  useEffect(() => {
    if (user) fetchLeaderboard();
  }, [user, fetchLeaderboard]);

  useEffect(() => {
    if (!user) return;
    const id = setInterval(fetchLeaderboard, 30_000);
    return () => clearInterval(id);
  }, [user, fetchLeaderboard]);

  useEffect(() => {
    if (!user) return;
    api.statsOverview().then(setStats).catch(() => {});
  }, [user]);

  useEffect(() => {
    if (!user || data.length < 2 || opponentFetched.current) return;
    const opponent = data.find((e) => e.user_id !== user.user_id);
    if (!opponent) return;
    opponentFetched.current = true;
    const end = new Date().toISOString().slice(0, 10);
    const start = new Date(Date.now() - 30 * 86_400_000).toISOString().slice(0, 10);
    api.listActivities({ user_id: opponent.user_id, start_date: start, end_date: end })
      .then((acts) => {
        const sorted = [...acts].sort((a, b) => b.date.localeCompare(a.date) || b.id - a.id);
        setOpponentActivities(sorted.slice(0, 5));
      })
      .catch(() => {});
  }, [user, data]);

  if (loading || !user) return null;

  const opponent = data.find((e) => e.user_id !== user.user_id);

  const trendUsers = stats
    ? [
        { user_id: user.user_id, name: user.name, colorClass: "bg-indigo-500" },
        ...stats.streaks
          .filter((s) => s.user_id !== user.user_id)
          .map((s) => ({ user_id: s.user_id, name: s.name, colorClass: "bg-violet-400" })),
      ]
    : [];

  const sortedStreaks = stats
    ? [...stats.streaks].sort((a) => (a.user_id === user.user_id ? -1 : 1))
    : [];

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav />
      <main className="max-w-2xl mx-auto px-4 pt-4 pb-24 space-y-4">

        {/* Period tabs */}
        <div className="flex gap-1.5 bg-white rounded-2xl p-1.5 border border-gray-100 shadow-sm">
          {(["daily", "weekly", "monthly"] as Period[]).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`flex-1 py-2 text-sm font-medium rounded-xl transition-colors ${
                period === p
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {p === "daily" ? "Today" : p === "weekly" ? "This Week" : "This Month"}
            </button>
          ))}
        </div>

        {/* Leaderboard */}
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
            Leaderboard
          </h2>
          <LeaderboardTable data={data} loading={fetching} currentUserId={user.user_id} />
        </div>

        {/* Streaks */}
        {sortedStreaks.length > 0 && (
          <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
              Active Streaks
            </h2>
            <div className="grid grid-cols-2 gap-3">
              {sortedStreaks.map((s, i) => (
                <div
                  key={s.user_id}
                  className={`rounded-xl p-4 text-center ${i === 0 ? "bg-indigo-50" : "bg-gray-50"}`}
                >
                  <div className={`text-4xl font-bold ${i === 0 ? "text-indigo-600" : "text-gray-700"}`}>
                    {s.streak}
                  </div>
                  <div className="text-sm font-medium text-gray-700 mt-1">{s.name}</div>
                  <div className="text-xs text-gray-400">day streak</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 8-Week Trend */}
        {stats && trendUsers.length > 0 && (
          <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
              8-Week Trend
            </h2>
            <TrendChart weeks={stats.weekly_trend} users={trendUsers} />
          </div>
        )}

        {/* Opponent feed */}
        {opponent && (
          <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
              {opponent.name}&apos;s Recent Activity
            </h2>
            {opponentActivities.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-3">No recent activities</p>
            ) : (
              <div className="divide-y divide-gray-50">
                {opponentActivities.map((a) => (
                  <div key={a.id} className="py-3 flex items-center justify-between first:pt-0 last:pb-0">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{a.activity_type}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{a.date}</p>
                    </div>
                    <span className="text-sm font-mono font-medium text-gray-600">
                      {a.step_equivalent_calculated.toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
