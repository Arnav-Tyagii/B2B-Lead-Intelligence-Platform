import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";

/** Bordered, sharp-cornered container. Optional hard-shadow lift on hover. */
const cardVariants = cva("border border-ink bg-paper", {
  variants: {
    interactive: {
      true: "hard-shadow-hover hover:bg-neutral-100 cursor-pointer",
      false: "",
    },
    padding: {
      none: "p-0",
      sm: "p-4",
      md: "p-6",
      lg: "p-8",
    },
  },
  defaultVariants: { interactive: false, padding: "md" },
});

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

export function Card({ className, interactive, padding, ...props }: CardProps) {
  return (
    <div className={cn(cardVariants({ interactive, padding }), className)} {...props} />
  );
}
