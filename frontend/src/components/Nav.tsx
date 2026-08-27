"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/api";

const LINKS = [
  { href: "/dashboard", label: "State" },
  { href: "/plan", label: "Constitution" },
  { href: "/import", label: "Data" },
  { href: "/checkin", label: "Check-in" },
  { href: "/weekly", label: "Weekly" },
  { href: "/chat", label: "Coach" },
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
      className={`text-sm transition whitespace-nowrap ${
        path === href ? "text-blue-400 font-medium" : "text-slate-400 hover:text-white"
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
          <nav className="hidden items-center gap-5 md:flex">
            {LINKS.map((l) => (
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
          <button
            onClick={logout}
            className="rounded-lg px-3 py-1.5 text-sm text-slate-400 transition hover:bg-slate-800 hover:text-white"
          >
            Log out
          </button>
        </div>
      </div>
      <nav className="flex gap-4 overflow-x-auto border-t border-slate-800/50 px-4 py-2 md:hidden">
        {LINKS.map((l) => (
          <span key={l.href}>{link(l.href, l.label)}</span>
        ))}
      </nav>
    </header>
  );
}
