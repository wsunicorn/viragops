"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Sparkles } from "lucide-react";

const LINKS = [
  { href: "/", label: "Tổng quan" },
  { href: "/demo", label: "Demo hỏi-đáp" },
  { href: "/dashboard", label: "Thực nghiệm" },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="fixed inset-x-0 top-0 z-50 flex justify-center px-4 pt-4">
      <nav className="flex w-full max-w-5xl items-center justify-between rounded-full border border-white/10 bg-background/60 px-4 py-2.5 shadow-lg shadow-black/20 backdrop-blur-xl">
        <Link href="/" className="flex items-center gap-2 pl-1 text-sm font-semibold tracking-tight">
          <Sparkles className="size-4 text-primary" aria-hidden />
          <span className="text-gradient">viRAGops</span>
        </Link>
        <div className="flex items-center gap-1">
          {LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-full px-3.5 py-1.5 text-sm transition-colors",
                  active
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
