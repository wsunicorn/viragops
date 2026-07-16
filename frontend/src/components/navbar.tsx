"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, useScroll, useSpring } from "motion/react";
import { cn } from "@/lib/utils";
import { Hexagon } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

const LINKS = [
  { href: "/", label: "Tổng quan" },
  { href: "/demo", label: "Demo hỏi-đáp" },
  { href: "/dashboard", label: "Thực nghiệm" },
];

export function Navbar() {
  const pathname = usePathname();
  const { scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, { stiffness: 120, damping: 28, restDelta: 0.001 });

  return (
    <header className="fixed inset-x-0 top-0 z-50 flex justify-center px-4 pt-4">
      <nav className="glass-edge relative flex w-full max-w-5xl items-center justify-between overflow-hidden rounded-full bg-background/60 px-4 py-2.5 backdrop-blur-xl">
        <Link href="/" className="flex items-center gap-2 pl-1 text-sm font-semibold tracking-tight">
          <Hexagon className="size-4 text-accent" aria-hidden />
          <span>
            vi<span className="text-accent">RAG</span>ops
          </span>
        </Link>
        <div className="flex items-center gap-1">
          {LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "relative rounded-full px-3.5 py-1.5 text-sm transition-colors",
                  active ? "text-accent" : "text-muted-foreground hover:bg-foreground/5 hover:text-foreground",
                )}
              >
                {active ? (
                  <motion.span
                    layoutId="nav-active"
                    className="absolute inset-0 rounded-full bg-accent/12"
                    transition={{ type: "spring", stiffness: 350, damping: 30 }}
                  />
                ) : null}
                <span className="relative">{link.label}</span>
              </Link>
            );
          })}
          <span className="mx-1 h-4 w-px bg-border" aria-hidden />
          <ThemeToggle />
        </div>
        {/* thanh tiến độ cuộn trang — nằm ở mép dưới pill */}
        <motion.span
          aria-hidden
          className="absolute inset-x-4 bottom-0 h-px origin-left bg-accent/70"
          style={{ scaleX: progress }}
        />
      </nav>
    </header>
  );
}
