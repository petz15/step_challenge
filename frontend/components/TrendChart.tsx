"use client";

interface WeekData {
  week_start: string;
  totals: Record<string, number>;
}

interface TrendUser {
  user_id: number;
  name: string;
  colorClass: string;
}

export default function TrendChart({
  weeks,
  users,
}: {
  weeks: WeekData[];
  users: TrendUser[];
}) {
  const allVals = weeks.flatMap((w) => users.map((u) => w.totals[String(u.user_id)] ?? 0));
  const maxVal = Math.max(...allVals, 1);

  const fmt = (dateStr: string) => {
    const d = new Date(dateStr + "T00:00:00");
    return `${d.getMonth() + 1}/${d.getDate()}`;
  };

  return (
    <div>
      <div className="flex items-end gap-1 h-28">
        {weeks.map((week) => (
          <div key={week.week_start} className="flex-1 flex items-end gap-0.5">
            {users.map((u) => {
              const steps = week.totals[String(u.user_id)] ?? 0;
              const pct = (steps / maxVal) * 100;
              return (
                <div
                  key={u.user_id}
                  className={`flex-1 rounded-t-sm min-h-[2px] ${u.colorClass}`}
                  style={{ height: `${Math.max(pct, 1)}%` }}
                  title={`${u.name}: ${steps.toLocaleString()}`}
                />
              );
            })}
          </div>
        ))}
      </div>

      <div className="flex gap-1 mt-2">
        {weeks.map((w) => (
          <div key={w.week_start} className="flex-1 text-center">
            <span className="text-[10px] text-gray-400">{fmt(w.week_start)}</span>
          </div>
        ))}
      </div>

      <div className="flex gap-5 justify-center mt-3">
        {users.map((u) => (
          <div key={u.user_id} className="flex items-center gap-1.5">
            <div className={`w-2.5 h-2.5 rounded-sm ${u.colorClass}`} />
            <span className="text-xs text-gray-500">{u.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
