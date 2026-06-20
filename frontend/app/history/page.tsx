"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ActivityResponse } from "@/lib/api";
import Nav from "@/components/Nav";
import Link from "next/link";

export default function HistoryPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [activities, setActivities] = useState<ActivityResponse[]>([]);
  const [fetching, setFetching] = useState(true);
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().slice(0, 10);
  });
  const [endDate] = useState(new Date().toISOString().slice(0, 10));
  const [deleting, setDeleting] = useState<number | null>(null);

  useEffect(() => {
    if (!loading && !user) router.replace("/");
  }, [user, loading, router]);

  const fetchHistory = useCallback(async () => {
    setFetching(true);
    try {
      const data = await api.listActivities({ start_date: startDate, end_date: endDate });
      setActivities(data);
    } catch {
      //
    } finally {
      setFetching(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    if (user) fetchHistory();
  }, [user, fetchHistory]);

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this activity?")) return;
    setDeleting(id);
    try {
      await api.deleteActivity(id);
      setActivities((prev) => prev.filter((a) => a.id !== id));
    } catch {
      alert("Failed to delete");
    } finally {
      setDeleting(null);
    }
  };

  if (loading || !user) return null;

  return (
    <div className="min-h-screen">
      <Nav />
      <main className="max-w-2xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Activity History</h1>
          <Link
            href="/log"
            className="text-sm bg-indigo-600 text-white px-3 py-1.5 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            + Log
          </Link>
        </div>

        <div className="mb-4 flex gap-3 items-center">
          <label className="text-sm text-gray-600">From:</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <span className="text-gray-400 text-sm">to today</span>
        </div>

        {fetching ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : activities.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <p className="text-4xl mb-3">📭</p>
            <p>No activities in this period.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {activities.map((a) => (
              <div
                key={a.id}
                className="flex items-center gap-3 p-4 bg-white rounded-xl border border-gray-200 group"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <span className="font-medium text-gray-900">{a.activity_type}</span>
                    <span className="text-xs text-gray-400">{a.date}</span>
                    {a.source === "garmin_api" && (
                      <span className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded font-medium">Garmin</span>
                    )}
                  </div>
                  <div className="text-sm text-gray-500 mt-0.5">
                    {a.duration_minutes && `${a.duration_minutes} min`}
                    {a.distance_km && `${a.distance_km} km`}
                    {a.notes && ` · ${a.notes}`}
                  </div>
                </div>
                <div className="text-right">
                  <span className="font-mono font-medium text-gray-800">
                    {a.step_equivalent_calculated.toLocaleString()}
                  </span>
                  <span className="text-xs text-gray-400 ml-1">steps</span>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Link
                    href={`/activity/${a.id}`}
                    className="p-1.5 text-gray-400 hover:text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors"
                    title="Edit"
                  >
                    ✏️
                  </Link>
                  <button
                    onClick={() => handleDelete(a.id)}
                    disabled={deleting === a.id}
                    className="p-1.5 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
                    title="Delete"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
            <p className="text-xs text-gray-400 text-center pt-2">
              {activities.length} activities ·{" "}
              {activities.reduce((s, a) => s + a.step_equivalent_calculated, 0).toLocaleString()} total steps
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
