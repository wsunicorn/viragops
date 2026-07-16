"use client";

import { useEffect, useRef } from "react";
import { useInView, useMotionValue, useSpring } from "motion/react";

/**
 * Số đếm chạy lên khi cuộn vào tầm nhìn — useMotionValue + useSpring,
 * ghi textContent trực tiếp qua ref (không setState mỗi frame).
 */
export function CountUp({
  value,
  decimals = 0,
  suffix = "",
  className,
}: {
  value: number;
  decimals?: number;
  suffix?: string;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const mv = useMotionValue(0);
  const spring = useSpring(mv, { stiffness: 60, damping: 20 });

  useEffect(() => {
    if (inView) mv.set(value);
  }, [inView, value, mv]);

  useEffect(() => {
    const unsub = spring.on("change", (v) => {
      if (ref.current) ref.current.textContent = v.toFixed(decimals) + suffix;
    });
    return unsub;
  }, [spring, decimals, suffix]);

  return (
    <span ref={ref} className={className}>
      {(0).toFixed(decimals) + suffix}
    </span>
  );
}
