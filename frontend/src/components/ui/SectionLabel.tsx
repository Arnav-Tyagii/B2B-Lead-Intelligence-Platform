import { cn } from "@/lib/cn";

/** Uppercase mono kicker label used above sections and as column headers. */
export function SectionLabel({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn(
        "font-mono text-xs uppercase tracking-widest text-neutral-500",
        className,
      )}
      {...props}
    />
  );
}
