"use client";

import { useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import { motion, AnimatePresence } from "motion/react";
import { Moon, Sun } from "lucide-react";

// mounted-guard không dùng setState-trong-effect (lint react 19):
// server snapshot = false, client snapshot = true.
function useMounted() {
  return useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
}

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const mounted = useMounted();
  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      // label chỉ đổi theo theme SAU khi mounted — server không biết theme
      // (localStorage), label động lúc SSR chính là nguồn hydration mismatch
      aria-label={mounted ? (isDark ? "Chuyển sang nền sáng" : "Chuyển sang nền tối") : "Chuyển giao diện sáng/tối"}
      className="relative flex size-8 cursor-pointer items-center justify-center overflow-hidden rounded-full text-muted-foreground transition-colors hover:bg-foreground/5 hover:text-foreground active:scale-95"
    >
      {mounted ? (
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={isDark ? "moon" : "sun"}
            initial={{ y: 10, opacity: 0, rotate: -30 }}
            animate={{ y: 0, opacity: 1, rotate: 0 }}
            exit={{ y: -10, opacity: 0, rotate: 30 }}
            transition={{ type: "spring", stiffness: 350, damping: 26 }}
            className="flex"
          >
            {isDark ? <Moon className="size-4" /> : <Sun className="size-4" />}
          </motion.span>
        </AnimatePresence>
      ) : (
        <Moon className="size-4 opacity-0" aria-hidden />
      )}
    </button>
  );
}
