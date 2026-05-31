import type { Metadata } from "next";
import "@/styles/globals.css";
import AppShell from "@/layouts/AppShell";

export const metadata: Metadata = {
  title: "YieldLens | Bloomberg Terminal for Bond Investors",
  description:
    "Professional-grade fixed income intelligence platform. Real-time bond analytics, yield curves, credit analysis, and AI-powered insights.",
  keywords: [
    "bonds",
    "fixed income",
    "yield curve",
    "treasury",
    "credit analysis",
    "Bloomberg terminal",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-black text-text font-sans antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
