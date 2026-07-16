"use client";

import dynamic from "next/dynamic";
import { useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import { DARK_COLORS, LIGHT_COLORS } from "./core-colors";

/**
 * Client wrapper cho canvas 3D: dynamic import ssr:false (WebGL không
 * render trên server), fallback là một "core" CSS tĩnh cùng bố cục để
 * không giật layout khi bundle three.js tải xong. Tôn trọng
 * prefers-reduced-motion — vẫn render vật thể nhưng đứng yên.
 */
const KnowledgeCore = dynamic(() => import("./knowledge-core"), {
  ssr: false,
  loading: () => <StaticCoreFallback />,
});

function StaticCoreFallback() {
  return (
    <div className="flex size-full items-center justify-center" aria-hidden>
      <div className="relative size-56 sm:size-72">
        <div className="absolute inset-0 rounded-full border border-accent/25" />
        <div className="absolute inset-6 rounded-full border border-accent/15" />
        <div className="absolute inset-0 m-auto size-24 rounded-full bg-accent/15 blur-2xl" />
      </div>
    </div>
  );
}

const REDUCED_QUERY = "(prefers-reduced-motion: reduce)";

function subscribeReducedMotion(callback: () => void) {
  const mq = window.matchMedia(REDUCED_QUERY);
  mq.addEventListener("change", callback);
  return () => mq.removeEventListener("change", callback);
}

/** Subscribe media query qua useSyncExternalStore (không setState trong
 * effect — đúng khuyến nghị react-hooks/set-state-in-effect). */
function useReducedMotion(): boolean {
  return useSyncExternalStore(
    subscribeReducedMotion,
    () => window.matchMedia(REDUCED_QUERY).matches,
    () => false, // server snapshot — canvas chỉ render client (ssr:false)
  );
}

export function HeroVisual() {
  const reduced = useReducedMotion();
  const { resolvedTheme } = useTheme();
  const isLight = resolvedTheme === "light";

  return (
    <div className="relative size-full min-h-72 sm:min-h-96" aria-hidden>
      {/* quầng sáng accent phía sau vật thể — 1 màu duy nhất, không orb tím */}
      <div className="absolute inset-0 m-auto size-72 rounded-full bg-accent/10 blur-[110px]" />
      {/* key theo theme: remount canvas để material nhận bảng màu mới */}
      <KnowledgeCore key={isLight ? "light" : "dark"} animate={!reduced} colors={isLight ? LIGHT_COLORS : DARK_COLORS} />
    </div>
  );
}
