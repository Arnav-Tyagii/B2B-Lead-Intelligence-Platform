import type { Metadata } from "next";
import { Masthead } from "@/components/layout/Masthead";
import { Footer } from "@/components/layout/Footer";
import { BackendWarmer } from "@/components/system/BackendWarmer";
import "./globals.css";

export const metadata: Metadata = {
  title: "The Lead Intelligence Times",
  description:
    "Account-based GTM intelligence — firmographics, GenAI enrichment, and ICP fit scoring, presented as an editorial book of business.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col">
        {/* Skip link for keyboard/screen-reader users. */}
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:bg-ink focus:px-4 focus:py-2 focus:font-mono focus:text-xs focus:uppercase focus:tracking-widest focus:text-paper"
        >
          Skip to content
        </a>
        <BackendWarmer />
        <Masthead />
        <main id="main" className="flex-1">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
