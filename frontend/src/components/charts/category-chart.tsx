"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CategoryRow } from "@/lib/data/eval";

const GRID = "oklch(1 0 0 / 8%)";
const AXIS = "oklch(0.66 0.03 275)";

export function CategoryChart({ data }: { data: CategoryRow[] }) {
  const chartData = data.map((d) => ({
    category: d.category,
    "Refusal Acc": d.refusalAcc,
    "Citation Acc": d.citationAcc,
    "Recall@5": d.recallAt5,
  }));

  return (
    <ResponsiveContainer width="100%" height={340}>
      <BarChart data={chartData} margin={{ left: -12, right: 12, top: 8, bottom: 8 }}>
        <CartesianGrid vertical={false} stroke={GRID} />
        <XAxis dataKey="category" tick={{ fill: AXIS, fontSize: 11 }} />
        <YAxis domain={[0, 1]} tick={{ fill: AXIS, fontSize: 11 }} />
        <Tooltip
          cursor={{ fill: "oklch(1 0 0 / 4%)" }}
          contentStyle={{
            background: "oklch(0.19 0.025 275)",
            border: "1px solid oklch(1 0 0 / 10%)",
            borderRadius: 10,
            fontSize: 12,
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: AXIS }} />
        <Bar dataKey="Recall@5" fill="oklch(0.72 0.16 288)" radius={[4, 4, 0, 0]} maxBarSize={22} />
        <Bar dataKey="Citation Acc" fill="oklch(0.78 0.15 340)" radius={[4, 4, 0, 0]} maxBarSize={22} />
        <Bar dataKey="Refusal Acc" fill="oklch(0.75 0.14 195)" radius={[4, 4, 0, 0]} maxBarSize={22} />
      </BarChart>
    </ResponsiveContainer>
  );
}
