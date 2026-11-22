import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIFRE — AI Financial Requirements Engineering",
  description: "Agentic AI platform for financial requirements engineering with adaptive interviews, compliance analysis, and SDLC selection.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="antialiased bg-slate-50 text-slate-900 font-sans">{children}</body>
    </html>
  );
}
