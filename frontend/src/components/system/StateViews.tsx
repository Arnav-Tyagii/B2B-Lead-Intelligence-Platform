import { AlertTriangle, Inbox } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { SectionLabel } from "@/components/ui/SectionLabel";

/** Newsprint error panel with a retry action. */
export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="border border-ink bg-paper p-8 text-center">
      <AlertTriangle className="mx-auto h-8 w-8 stroke-1 text-accent" aria-hidden="true" />
      <SectionLabel className="mt-4 text-accent">Stop the Press</SectionLabel>
      <p className="mx-auto mt-2 max-w-md font-body text-sm text-neutral-700">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" className="mt-6" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

/** Newsprint empty-result panel. */
export function EmptyState({ message }: { message: string }) {
  return (
    <div className="border border-divider bg-paper p-12 text-center">
      <Inbox className="mx-auto h-8 w-8 stroke-1 text-neutral-400" aria-hidden="true" />
      <p className="mt-4 font-body text-sm text-neutral-600">{message}</p>
    </div>
  );
}
