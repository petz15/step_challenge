"use client";

import { LeaderboardEntry } from "@/lib/api";

export default function LeaderboardTable({
  data,
  loading,
  currentUserId,
}: {
  data: LeaderboardEntry[];
  loading: boolean;
  currentUserId?: number;
}) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2].map((i) => (
          <div key={i} className="h-20 bg-gray-100 rounded-2xl animate-pulse" />
        ))}
      </div>
    );
  }

  const maxSteps = Math.max(...data.map((e) => e.total_steps), 1);
  const diff = data.length >= 2 ? data[0].total_steps - data[1].total_steps : 0;

  return (
    <div className="space-y-3">
      {data.map((entry, i) => {
        const isLeader = i === 0;
        const isMe = entry.user_id === currentUserId;
        const barPct = (entry.total_steps / maxSteps) * 100;

        return (
          <div
            key={entry.user_id}
            className={`p-4 rounded-2xl border ${
              isLeader ? "border-indigo-100 bg-indigo-50" : "border-gray-100 bg-white"
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className={`text-xs font-bold tabular-nums w-4 ${isLeader ? "text-indigo-400" : "text-gray-300"}`}>
                  {entry.rank}
                </span>
                <span className="font-semibold text-gray-900">{entry.name}</span>
                {isMe && <span className="text-xs text-gray-400">you</span>}
              </div>
              <div>
                <span className="font-mono font-semibold text-gray-900">
                  {entry.total_steps.toLocaleString()}
                </span>
                <span className="text-xs text-gray-400 ml-1">steps</span>
              </div>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  isLeader ? "bg-indigo-500" : "bg-gray-300"
                }`}
                style={{ width: `${barPct}%` }}
              />
            </div>
          </div>
        );
      })}

      {data.length >= 2 && (
        <p className="text-xs text-gray-400 text-center pt-1">
          {diff > 0
            ? `${data[0].name} leads by ${diff.toLocaleString()} steps`
            : "Tied"}
        </p>
      )}
    </div>
  );
}
