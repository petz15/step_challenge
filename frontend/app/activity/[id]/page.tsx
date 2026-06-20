"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ActivityResponse } from "@/lib/api";
import Nav from "@/components/Nav";

const ACTIVITY_TYPES = ["Walking", "Running", "Hiking", "Cycling", "Climbing", "Strength", "Manual Steps"];

export default function EditActivityPage({ params }: PageProps<"/activity/[id]">) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [activity, setActivity] = useState<ActivityResponse | null>(null);
  const [activityType, setActivityType] = useState("");
  const [duration, setDuration] = useState("");
  const [distance, setDistance] = useState("");
  const [manualSteps, setManualSteps] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading && !user) router.replace("/");
  }, [user, loading, router]);

  useEffect(() => {
    if (!user) return;
    params.then(({ id }) => {
      api.getActivity(Number(id)).then((a) => {
        setActivity(a);
        setActivityType(a.activity_type);
        setDuration(a.duration_minutes?.toString() ?? "");
        setDistance(a.distance_km?.toString() ?? "");
        setManualSteps(a.manual_steps?.toString() ?? "");
        setNotes(a.notes ?? "");
      }).catch(() => router.replace("/history"));
    });
  }, [user, params, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activity) return;
    setError("");
    setSubmitting(true);
    try {
      await api.updateActivity(activity.id, {
        activity_type: activityType,
        duration_minutes: duration ? Number(duration) : null,
        distance_km: distance ? Number(distance) : null,
        manual_steps: manualSteps ? Number(manualSteps) : null,
        notes: notes || null,
      });
      router.push("/history");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || !user || !activity) return null;

  return (
    <div className="min-h-screen">
      <Nav />
      <main className="max-w-lg mx-auto px-4 py-6 pb-24">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Edit Activity</h1>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-200 p-6 space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Activity Type</label>
            <select
              value={activityType}
              onChange={(e) => setActivityType(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {ACTIVITY_TYPES.map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Duration (min)</label>
              <input
                type="number"
                min="1"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Distance (km)</label>
              <input
                type="number"
                min="0.1"
                step="0.1"
                value={distance}
                onChange={(e) => setDistance(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Manual Steps</label>
            <input
              type="number"
              min="1"
              value={manualSteps}
              onChange={(e) => setManualSteps(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {error && <p className="text-red-600 text-sm">{error}</p>}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 bg-indigo-600 text-white py-2.5 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {submitting ? "Saving…" : "Save Changes"}
            </button>
            <button
              type="button"
              onClick={() => router.push("/history")}
              className="px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
