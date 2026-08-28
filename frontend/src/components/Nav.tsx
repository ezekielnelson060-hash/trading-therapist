"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/api";

const LINKS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/monitor", label: "Monitor" },
  { href: "/patterns", label: "Patterns" },
  { href: "/plan", label: "Plan" },
  { href: "/chat", label: "Coach" },
  { href: "/weekly", label: "Reports" },
  { href: "/import", label: "Connections" },
  { href: "/alerts", label: "Alerts" },
  { href: "/teams", label: "Teams" },
  { href: "/billing", label: "Billing" },
];

export default function Nav({ llmBadge }: { llmBadge?: boolean }) {
  const path = usePathname();
  const router = useRouter();

  function logout() {
    clearToken();
    router.push("/login");
  }

  const link = (href: string, label: string) => (
    <Link
      href={href}
      className={`whitespace-nowrap text-sm transition ${
        path === href ? "font-medium text-blue-400" : "text-slate-400 hover:text-white"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-[#0b0f14]/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3.5">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="text-lg font-bold tracking-tight text-white">
            TiltShield
          </Link>
          <nav className="hidden items-center gap-4 lg:flex">
            {LINKS.slice(0, 7).map((l) => (
              <span key={l.href}>{link(l.href, l.label)}</span>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          {llmBadge && (
            <span className="hidden rounded-full bg-emerald-900/40 px-2.5 py-0.5 text-xs text-emerald-300 sm:inline">
              LLM live
            </span>
          )}
          <Link href="/billing" className="hidden text-sm text-slate-500 hover:text-white sm:inline">
            Billing
          </Link>
          <button
            onClick={logout}
            className="rounded-lg px-3 py-1.5 text-sm text-slate-400 transition hover:bg-slate-800 hover:text-white"
          >
            Log out
          </button>
        </div>
      </div>
      <nav className="flex gap-4 overflow-x-auto border-t border-slate-800/50 px-4 py-2 lg:hidden">
        {LINKS.map((l) => (
          <span key={l.href}>{link(l.href, l.label)}</span>
        ))}
      </nav>
    </header>
  );
}
