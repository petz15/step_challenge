"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, LeaderboardEntry } from "@/lib/api";
import Nav from "@/components/Nav";
import LeaderboardTable from "@/components/LeaderboardTable";

type Period = "daily" | "weekly" | "monthly";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [period, setPeriod] = useState<Period>("weekly");
  const [data, setData] = useState<LeaderboardEntry[]>([]);
  const [fetching, setFetching] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

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
      setLastRefresh(new Date());
    } catch {
      // silently fail on background refresh
    } finally {
      setFetching(false);
    }
  }, [period]);

  useEffect(() => {
    if (user) fetchLeaderboard();
  }, [user, fetchLeaderboard]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!user) return;
    const id = setInterval(fetchLeaderboard, 30_000);
    return () => clearInterval(id);
  }, [user, fetchLeaderboard]);

  if (loading || !user) return null;

  const periodLabel = { daily: "Today", weekly: "This Week", monthly: "This Month" }[period];

  return (
    <div className="min-h-screen">
      <Nav />
      <main className="max-w-2xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Leaderboard</h1>
          <button
            onClick={fetchLeaderboard}
            className="text-sm text-indigo-600 hover:text-indigo-800 transition-colors"
          >
            Refresh
          </button>
        </div>

        {/* Period tabs */}
        <div className="flex gap-2 mb-6 bg-gray-100 p-1 rounded-xl">
          {(["daily", "weekly", "monthly"] as Period[]).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`flex-1 py-2 text-sm font-medium rounded-lg capitalize transition-colors ${
                period === p ? "bg-white text-indigo-700 shadow-sm" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {p}
            </button>
          ))}
        </div>

        <p className="text-xs text-gray-400 mb-4">
          {periodLabel} · Last updated {lastRefresh.toLocaleTimeString()}
        </p>

        <LeaderboardTable data={data} loading={fetching} />
      </main>
    </div>
  );
}
