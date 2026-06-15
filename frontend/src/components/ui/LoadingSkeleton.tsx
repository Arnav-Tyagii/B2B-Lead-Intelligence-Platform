import { cn } from "@/lib/cn";

/**
 * Newsprint loading skeleton — sharp grey blocks that pulse. Used everywhere so
 * a Render cold start (~50s) never looks broken, just "printing".
 */
export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse bg-neutral-200", className)}
      aria-hidden="true"
      {...props}
    />
  );
}

/** A bordered card-shaped skeleton matching the account grid cells. */
export function CardSkeleton() {
  return (
    <div className="border border-divider p-6" aria-hidden="true">
      <Skeleton className="mb-4 h-3 w-24" />
      <Skeleton className="mb-2 h-6 w-3/4" />
      <Skeleton className="mb-6 h-4 w-1/2" />
      <Skeleton className="h-2 w-full" />
    </div>
  );
}
