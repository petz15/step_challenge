"use client";

import { LeaderboardEntry } from "@/lib/api";

const MEDALS = ["🥇", "🥈", "🥉"];

export default function LeaderboardTable({ data, loading }: { data: LeaderboardEntry[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2].map((i) => (
          <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {data.map((entry) => (
        <div
          key={entry.user_id}
          className={`flex items-center gap-4 p-4 rounded-xl border ${
            entry.rank === 1 ? "border-yellow-200 bg-yellow-50" : "border-gray-200 bg-white"
          }`}
        >
          <span className="text-2xl w-8 text-center">
            {MEDALS[entry.rank - 1] ?? `#${entry.rank}`}
          </span>
          <div className="flex-1 min-w-0">
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-semibold text-gray-900 text-lg">{entry.name}</span>
              <span className="font-mono text-gray-700 font-medium">
                {entry.total_steps.toLocaleString()} steps
              </span>
            </div>
            {entry.goal && (
              <div className="mt-1.5">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Goal progress</span>
                  <span>{entry.goal_progress ?? 0}%</span>
                </div>
                <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full transition-all"
                    style={{ width: `${Math.min(entry.goal_progress ?? 0, 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
