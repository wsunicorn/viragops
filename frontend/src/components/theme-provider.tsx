"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";
import type { ReactNode } from "react";

/**
 * next-themes gắn/gỡ class "dark" trên <html> TRƯỚC khi React hydrate
 * (inline script) — vì vậy <html> phải có suppressHydrationWarning
 * (layout.tsx). defaultTheme="dark" giữ đúng cá tính cinematic hiện tại;
 * user chọn light sẽ được nhớ qua localStorage.
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  return (
    <NextThemesProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange>
      {children}
    </NextThemesProvider>
  );
}
