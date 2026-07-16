"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CategoryRow } from "@/lib/data/eval";
import {
  CURSOR_FILL,
  TOOLTIP_CONTENT_STYLE,
  TOOLTIP_ITEM_STYLE,
  TOOLTIP_LABEL_STYLE,
  TOOLTIP_WRAPPER_STYLE,
} from "./chart-theme";

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
        <CartesianGrid vertical={false} />
        <XAxis dataKey="category" tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
        <Tooltip
          cursor={CURSOR_FILL}
          contentStyle={TOOLTIP_CONTENT_STYLE}
          labelStyle={TOOLTIP_LABEL_STYLE}
          itemStyle={TOOLTIP_ITEM_STYLE}
          wrapperStyle={TOOLTIP_WRAPPER_STYLE}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="Recall@5" className="chart-fill-2" radius={[4, 4, 0, 0]} maxBarSize={22} />
        <Bar dataKey="Citation Acc" className="chart-fill-3" radius={[4, 4, 0, 0]} maxBarSize={22} />
        <Bar dataKey="Refusal Acc" className="chart-fill-1" radius={[4, 4, 0, 0]} maxBarSize={22} />
      </BarChart>
    </ResponsiveContainer>
  );
}
