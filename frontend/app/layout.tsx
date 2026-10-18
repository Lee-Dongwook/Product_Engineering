import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SCM Inventory Optimization Platform",
  description: "AI-driven inventory forecasting and multi-agent purchase order management",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        {children}
      </body>
    </html>
  );
}
