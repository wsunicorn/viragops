"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PromptSmokeResult } from "@/lib/data/prompts";
import {
  CURSOR_FILL,
  MONO_TICK,
  TOOLTIP_CONTENT_STYLE,
  TOOLTIP_ITEM_STYLE,
  TOOLTIP_LABEL_STYLE,
  TOOLTIP_WRAPPER_STYLE,
} from "./chart-theme";

export function PromptChart({ data }: { data: PromptSmokeResult[] }) {
  const chartData = data.map((d) => ({ name: d.version.replace("_v1", ""), value: d.refusalAcc, best: d.best }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24, top: 8, bottom: 8 }}>
        <CartesianGrid horizontal={false} />
        <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 11 }} tickFormatter={(v) => v.toFixed(1)} />
        <YAxis type="category" dataKey="name" width={140} tick={MONO_TICK} />
        <Tooltip
          cursor={CURSOR_FILL}
          contentStyle={TOOLTIP_CONTENT_STYLE}
          labelStyle={TOOLTIP_LABEL_STYLE}
          itemStyle={TOOLTIP_ITEM_STYLE}
          wrapperStyle={TOOLTIP_WRAPPER_STYLE}
          formatter={(v) => Number(v).toFixed(2)}
        />
        <Bar dataKey="value" radius={[0, 6, 6, 0]} maxBarSize={20}>
          {chartData.map((d, i) => (
            <Cell key={i} className={d.best ? "chart-fill-1" : "chart-fill-dim"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
