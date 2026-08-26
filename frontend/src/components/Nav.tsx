"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/api";

const LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/chat", label: "Therapist" },
  { href: "/plan", label: "Plan" },
  { href: "/import", label: "Import" },
];

export default function Nav() {
  const pathname = usePathname();
  const router = useRouter();

  function logout() {
    clearToken();
    router.push("/login");
  }

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/dashboard" className="text-sm font-bold tracking-tight text-white">
          Trading Therapist
        </Link>
        <nav className="flex flex-wrap items-center gap-1">
          {LINKS.map((l) => {
            const active = pathname === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`rounded-lg px-3 py-1.5 text-sm transition ${
                  active
                    ? "bg-blue-600/20 text-blue-300"
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
          <button
            type="button"
            onClick={logout}
            className="ml-2 rounded-lg px-3 py-1.5 text-sm text-slate-500 transition hover:bg-slate-800 hover:text-white"
          >
            Log out
          </button>
        </nav>
      </div>
    </header>
  );
}
