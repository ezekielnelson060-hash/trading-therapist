import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Trading Therapist",
  description: "AI Trading Therapist + Behavioral Analytics",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
