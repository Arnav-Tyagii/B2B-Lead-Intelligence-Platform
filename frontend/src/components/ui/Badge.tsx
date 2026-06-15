import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";

/**
 * Uppercase mono badge. Tier variants encode the book's hierarchy:
 * Hot uses the editorial red (breaking-news accent), Warm solid ink,
 * Cold a quiet outline. `tone` lets callers pick directly.
 */
const badgeVariants = cva(
  "inline-flex items-center gap-1 border px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-widest",
  {
    variants: {
      tone: {
        hot: "border-accent bg-accent text-paper",
        warm: "border-ink bg-ink text-paper",
        cold: "border-ink bg-transparent text-ink",
        neutral: "border-ink bg-transparent text-ink",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, tone, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}

/** Convenience: map a tier string to its badge tone. */
export function tierTone(tier: string): NonNullable<BadgeProps["tone"]> {
  if (tier === "Hot") return "hot";
  if (tier === "Warm") return "warm";
  return "cold";
}
