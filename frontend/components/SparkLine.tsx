"use client";

interface DataPoint {
  date: string;
  value: number;
}

interface SparkLineProps {
  data: DataPoint[];
  label: string;
  unit?: string;
  decimals?: number;
  color?: string;
  minFloor?: number;
}

export default function SparkLine({
  data,
  label,
  unit = "",
  decimals = 0,
  color = "#4f46e5",
  minFloor,
}: SparkLineProps) {
  if (data.length === 0) return null;

  const values = data.map((d) => d.value);
  const last = values[values.length - 1];
  const prev = values[values.length - 2];
  const trendUp = prev !== undefined && last > prev;
  const trendDown = prev !== undefined && last < prev;

  const W = 300;
  const H = 52;
  const PAD = 4;

  const minVal = minFloor !== undefined ? Math.min(minFloor, ...values) : Math.min(...values) * 0.95;
  const maxVal = Math.max(...values);
  const range = maxVal - minVal || 1;

  const pts = values.map((v, i) => {
    const x = data.length === 1 ? W / 2 : (i / (data.length - 1)) * W;
    const y = H - PAD - ((v - minVal) / range) * (H - PAD * 2);
    return [x, y] as [number, number];
  });

  const polyline = pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const lastPt = pts[pts.length - 1];

  const firstDate = data[0]?.date
    ? new Date(data[0].date + "T00:00:00").toLocaleDateString("en", { month: "short", day: "numeric" })
    : "";

  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</span>
        <div className="flex items-baseline gap-1">
          <span className="text-xl font-bold text-gray-900">{last.toFixed(decimals)}</span>
          {unit && <span className="text-xs text-gray-400">{unit}</span>}
          {trendUp && <span className="text-xs text-emerald-500 ml-1">▲</span>}
          {trendDown && <span className="text-xs text-rose-400 ml-1">▼</span>}
        </div>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: "52px" }}>
        <polyline
          points={polyline}
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.85"
        />
        {lastPt && (
          <circle cx={lastPt[0].toFixed(1)} cy={lastPt[1].toFixed(1)} r="3" fill={color} />
        )}
      </svg>
      <div className="flex justify-between text-xs text-gray-400">
        <span>{firstDate}</span>
        <span>Today</span>
      </div>
    </div>
  );
}
