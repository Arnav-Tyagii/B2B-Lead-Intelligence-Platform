import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";

/**
 * Newsprint button. Sharp corners, uppercase tracked label, instant color
 * inversion on hover. Variants per DESIGN_SYSTEM.md (primary/secondary/ghost/link).
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 font-sans text-xs font-semibold uppercase tracking-widest transition-all duration-200 ease-out disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-2 focus-visible:ring-offset-paper",
  {
    variants: {
      variant: {
        primary:
          "border border-transparent bg-ink text-paper hover:border-ink hover:bg-paper hover:text-ink",
        secondary:
          "border border-ink bg-transparent text-ink hover:bg-ink hover:text-paper",
        ghost: "text-ink hover:bg-divider",
        link: "text-ink underline-offset-4 decoration-2 decoration-accent hover:underline",
      },
      size: {
        // 44px min height keeps touch targets accessible.
        sm: "min-h-[44px] px-3 py-2",
        md: "min-h-[44px] px-5 py-3",
        lg: "min-h-[48px] px-7 py-4 text-sm",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button className={cn(buttonVariants({ variant, size }), className)} {...props} />
  );
}

export { buttonVariants };
