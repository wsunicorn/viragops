import { RevealItem } from "@/components/reveal";
import { cn } from "@/lib/utils";

export function StatCard({
  value,
  label,
  className,
}: {
  value: string;
  label: string;
  className?: string;
}) {
  return (
    <RevealItem
      className={cn(
        "rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-sm transition-colors hover:border-white/20",
        className,
      )}
    >
      <div className="text-gradient text-3xl font-bold tracking-tight sm:text-4xl">{value}</div>
      <div className="mt-1.5 text-sm text-muted-foreground">{label}</div>
    </RevealItem>
  );
}
