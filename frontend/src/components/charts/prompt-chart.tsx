"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PromptSmokeResult } from "@/lib/data/prompts";

const GRID = "oklch(1 0 0 / 8%)";
const AXIS = "oklch(0.66 0.03 275)";
const BEST = "oklch(0.75 0.14 195)";
const BAR = "oklch(0.72 0.16 288)";

export function PromptChart({ data }: { data: PromptSmokeResult[] }) {
  const chartData = data.map((d) => ({ name: d.version.replace("_v1", ""), value: d.refusalAcc, best: d.best }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24, top: 8, bottom: 8 }}>
        <CartesianGrid horizontal={false} stroke={GRID} />
        <XAxis type="number" domain={[0, 1]} tick={{ fill: AXIS, fontSize: 11 }} tickFormatter={(v) => v.toFixed(1)} />
        <YAxis
          type="category"
          dataKey="name"
          width={140}
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
          formatter={(v) => Number(v).toFixed(2)}
        />
        <Bar dataKey="value" radius={[0, 6, 6, 0]} maxBarSize={20}>
          {chartData.map((d, i) => (
            <Cell key={i} fill={d.best ? BEST : BAR} fillOpacity={d.best ? 1 : 0.5} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
