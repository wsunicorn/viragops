"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { RetrievalConfigResult } from "@/lib/data/retrieval";

const GRID = "oklch(1 0 0 / 8%)";
const AXIS = "oklch(0.66 0.03 275)";
const BEST = "oklch(0.75 0.14 195)";
const BAR = "oklch(0.72 0.16 288)";

export function RetrievalChart({ data, metric = "recallAt5" }: { data: RetrievalConfigResult[]; metric?: keyof RetrievalConfigResult }) {
  const chartData = data.map((d) => ({ name: d.config, value: d[metric] as number, best: d.best }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24, top: 8, bottom: 8 }}>
        <CartesianGrid horizontal={false} stroke={GRID} />
        <XAxis type="number" domain={[0.8, 1]} tick={{ fill: AXIS, fontSize: 11 }} tickFormatter={(v) => v.toFixed(2)} />
        <YAxis
          type="category"
          dataKey="name"
          width={168}
          tick={{ fill: AXIS, fontSize: 11, fontFamily: "var(--font-geist-mono)" }}
        />
        <Tooltip
          cursor={{ fill: "oklch(1 0 0 / 4%)" }}
          contentStyle={{
            background: "oklch(0.19 0.025 275)",
            border: "1px solid oklch(1 0 0 / 10%)",
            borderRadius: 10,
            fontSize: 12,
          }}
          formatter={(v) => Number(v).toFixed(3)}
        />
        <Bar dataKey="value" radius={[0, 6, 6, 0]} maxBarSize={22}>
          {chartData.map((d, i) => (
            <Cell key={i} fill={d.best ? BEST : BAR} fillOpacity={d.best ? 1 : 0.55} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
