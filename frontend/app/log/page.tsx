"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ConversionRule } from "@/lib/api";
import Nav from "@/components/Nav";

function estimateSteps(
  activityType: string,
  duration: string,
  distance: string,
  manualSteps: string,
  rules: ConversionRule[]
): number {
  const rule = rules.find((r) => r.activity_type === activityType);
  if (!rule) return 0;
  if (manualSteps && Number(manualSteps) > 0) return Number(manualSteps);
  if (duration && Number(duration) > 0) return Math.round(Number(duration) * rule.conversion_per_minute);
  if (distance && Number(distance) > 0) return Math.round(Number(distance) * rule.conversion_per_km);
  return 0;
}

export default function LogActivityPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [rules, setRules] = useState<ConversionRule[]>([]);
  const [activityType, setActivityType] = useState("");
  const [duration, setDuration] = useState("");
  const [distance, setDistance] = useState("");
  const [manualSteps, setManualSteps] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (!loading && !user) router.replace("/");
  }, [user, loading, router]);

  useEffect(() => {
    if (user) api.getConversionRules().then((r) => {
      setRules(r);
      if (r.length > 0) setActivityType((prev) => prev || r[0].activity_type);
    }).catch(() => {});
  }, [user]);

  const preview = estimateSteps(activityType, duration, distance, manualSteps, rules);

  const handleSubmit = async (e: React.SyntheticEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!duration && !distance && !manualSteps) {
      setError("Enter duration, distance, or manual steps");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.createActivity({
        activity_type: activityType,
        duration_minutes: duration ? Number(duration) : null,
        distance_km: distance ? Number(distance) : null,
        manual_steps: manualSteps ? Number(manualSteps) : null,
        date,
        notes: notes || null,
      });
      setSuccess(`Logged! ${res.step_equivalent_calculated.toLocaleString()} step equivalents added.`);
      setDuration("");
      setDistance("");
      setManualSteps("");
      setNotes("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to log activity");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || !user) return null;

  return (
    <div className="min-h-screen">
      <Nav />
      <main className="max-w-lg mx-auto px-4 py-6 pb-24">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Log Activity</h1>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-200 p-6 space-y-5">
          {/* Activity Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Activity Type</label>
            <select
              value={activityType}
              onChange={(e) => { setActivityType(e.target.value); setDuration(""); setDistance(""); setManualSteps(""); }}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {rules.map((r) => <option key={r.activity_type}>{r.activity_type}</option>)}
            </select>
          </div>

          {activityType === "Manual Steps" ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Steps</label>
              <input
                type="number"
                min="1"
                value={manualSteps}
                onChange={(e) => setManualSteps(e.target.value)}
                placeholder="e.g. 8000"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Duration (min)</label>
                <input
                  type="number"
                  min="1"
                  value={duration}
                  onChange={(e) => { setDuration(e.target.value); if (e.target.value) setDistance(""); }}
                  placeholder="e.g. 45"
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
                  onChange={(e) => { setDistance(e.target.value); if (e.target.value) setDuration(""); }}
                  placeholder="e.g. 5.0"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          )}

          {/* Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Morning trail run"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Step preview */}
          {preview > 0 && (
            <div className="bg-indigo-50 rounded-xl p-4 text-center">
              <p className="text-sm text-indigo-600 font-medium">Estimated step equivalents</p>
              <p className="text-3xl font-bold text-indigo-700 mt-1">{preview.toLocaleString()}</p>
            </div>
          )}

          {error && <p className="text-red-600 text-sm">{error}</p>}
          {success && <p className="text-green-600 text-sm font-medium">{success}</p>}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 bg-indigo-600 text-white py-2.5 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {submitting ? "Logging…" : "Log Activity"}
            </button>
            <button
              type="button"
              onClick={() => router.push("/dashboard")}
              className="px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >
              View Leaderboard
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
