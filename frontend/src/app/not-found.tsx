import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { SectionLabel } from "@/components/ui/SectionLabel";

/** Newsprint 404 — styled like a missing edition. */
export default function NotFound() {
  return (
    <div className="mx-auto max-w-screen-xl px-4 py-24 text-center">
      <SectionLabel className="text-accent">Edition Not Found</SectionLabel>
      <h1 className="mt-4 font-serif text-7xl font-black tracking-tight lg:text-9xl">404</h1>
      <p className="mx-auto mt-4 max-w-md font-body text-lg text-neutral-600">
        This story has gone to press elsewhere. The page you’re looking for isn’t
        in today’s edition.
      </p>
      <Link href="/" className="mt-8 inline-block">
        <Button>Return to the Front Page</Button>
      </Link>
    </div>
  );
}
