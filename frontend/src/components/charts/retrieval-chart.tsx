"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { RetrievalConfigResult } from "@/lib/data/retrieval";
import {
  CURSOR_FILL,
  MONO_TICK,
  TOOLTIP_CONTENT_STYLE,
  TOOLTIP_ITEM_STYLE,
  TOOLTIP_LABEL_STYLE,
  TOOLTIP_WRAPPER_STYLE,
} from "./chart-theme";

export function RetrievalChart({ data, metric = "recallAt5" }: { data: RetrievalConfigResult[]; metric?: keyof RetrievalConfigResult }) {
  const chartData = data.map((d) => ({ name: d.config, value: d[metric] as number, best: d.best }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24, top: 8, bottom: 8 }}>
        <CartesianGrid horizontal={false} />
        <XAxis type="number" domain={[0.8, 1]} tick={{ fontSize: 11 }} tickFormatter={(v) => v.toFixed(2)} />
        <YAxis type="category" dataKey="name" width={168} tick={MONO_TICK} />
        <Tooltip
          cursor={CURSOR_FILL}
          contentStyle={TOOLTIP_CONTENT_STYLE}
          labelStyle={TOOLTIP_LABEL_STYLE}
          itemStyle={TOOLTIP_ITEM_STYLE}
          wrapperStyle={TOOLTIP_WRAPPER_STYLE}
          formatter={(v) => Number(v).toFixed(3)}
        />
        <Bar dataKey="value" radius={[0, 6, 6, 0]} maxBarSize={22}>
          {chartData.map((d, i) => (
            <Cell key={i} className={d.best ? "chart-fill-1" : "chart-fill-dim"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
