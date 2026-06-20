"use client";

import { useState } from "react";

interface PeriodResult {
  period_start: string;
  winner_user_id: number | null;
  scores: Record<string, number>;
}

interface ChallengeRecordProps {
  users: { user_id: number; name: string }[];
  weekly: {
    history: PeriodResult[];
    wins: Record<string, number>;
    ties: number;
  };
  monthly: {
    history: PeriodResult[];
    wins: Record<string, number>;
    ties: number;
  };
  currentUserId: number;
}

export default function ChallengeRecord({
  users,
  weekly,
  monthly,
  currentUserId,
}: ChallengeRecordProps) {
  const [view, setView] = useState<"weekly" | "monthly">("weekly");
  const data = view === "weekly" ? weekly : monthly;

  const me = users.find((u) => u.user_id === currentUserId);
  const opponent = users.find((u) => u.user_id !== currentUserId);

  const myWins = me ? (data.wins[String(me.user_id)] ?? 0) : 0;
  const oppWins = opponent ? (data.wins[String(opponent.user_id)] ?? 0) : 0;

  const dotStyle = (r: PeriodResult) => {
    if (r.winner_user_id === null) return "bg-gray-200";
    return r.winner_user_id === currentUserId ? "bg-indigo-500" : "bg-violet-400";
  };

  const periodLabel = (iso: string) => {
    const d = new Date(iso + "T00:00:00");
    return view === "weekly"
      ? d.toLocaleDateString("en", { month: "short", day: "numeric" })
      : d.toLocaleDateString("en", { month: "short", year: "2-digit" });
  };

  const total = myWins + oppWins + data.ties;
  const myPct = total > 0 ? (myWins / total) * 100 : 0;
  const oppPct = total > 0 ? (oppWins / total) * 100 : 0;

  return (
    <div>
      {/* Toggle */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-5">
        {(["weekly", "monthly"] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              view === v ? "bg-white text-gray-900 shadow-sm" : "text-gray-500"
            }`}
          >
            {v === "weekly" ? "Weekly" : "Monthly"}
          </button>
        ))}
      </div>

      {/* Win counts */}
      <div className="grid grid-cols-3 gap-2 mb-4 text-center">
        <div>
          <div className="text-3xl font-bold text-indigo-600">{myWins}</div>
          <div className="text-xs text-gray-500 mt-0.5">{me?.name ?? "You"}</div>
        </div>
        <div className="flex flex-col items-center justify-center">
          {data.ties > 0 && (
            <>
              <div className="text-lg font-semibold text-gray-300">{data.ties}</div>
              <div className="text-xs text-gray-400">Tied</div>
            </>
          )}
        </div>
        <div>
          <div className="text-3xl font-bold text-violet-500">{oppWins}</div>
          <div className="text-xs text-gray-500 mt-0.5">{opponent?.name ?? "Opponent"}</div>
        </div>
      </div>

      {/* Progress bar */}
      {total > 0 && (
        <div className="flex h-2 rounded-full overflow-hidden mb-5 gap-0.5">
          {myWins > 0 && (
            <div
              className="bg-indigo-500 rounded-l-full transition-all"
              style={{ width: `${myPct}%` }}
            />
          )}
          {data.ties > 0 && (
            <div
              className="bg-gray-200 transition-all"
              style={{ width: `${(data.ties / total) * 100}%` }}
            />
          )}
          {oppWins > 0 && (
            <div
              className="bg-violet-400 rounded-r-full transition-all"
              style={{ width: `${oppPct}%` }}
            />
          )}
        </div>
      )}

      {/* History dots */}
      {data.history.length > 0 && (
        <div className="flex gap-1.5 flex-wrap">
          {data.history.map((r) => (
            <div
              key={r.period_start}
              className={`w-5 h-5 rounded-full flex-shrink-0 ${dotStyle(r)}`}
              title={`${periodLabel(r.period_start)}${r.winner_user_id ? `: ${users.find((u) => u.user_id === r.winner_user_id)?.name} won` : ": tied"}`}
            />
          ))}
        </div>
      )}

      {/* Legend */}
      <div className="flex gap-4 mt-3 text-xs text-gray-400">
        <span>
          <span className="inline-block w-2 h-2 rounded-full bg-indigo-500 mr-1 align-middle" />
          {me?.name ?? "You"}
        </span>
        <span>
          <span className="inline-block w-2 h-2 rounded-full bg-violet-400 mr-1 align-middle" />
          {opponent?.name ?? "Opponent"}
        </span>
        {data.ties > 0 && (
          <span>
            <span className="inline-block w-2 h-2 rounded-full bg-gray-200 mr-1 align-middle" />
            Tie
          </span>
        )}
      </div>
    </div>
  );
}
