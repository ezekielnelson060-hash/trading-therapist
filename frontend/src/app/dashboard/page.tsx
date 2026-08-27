"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [behavioral, setBehavioral] = useState<any>(null);
  const [trades, setTrades] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const me = await api.me();
        setUser(me);
        const [s, b, t] = await Promise.all([
          api.summary().catch(() => null),
          api.behavioral().catch(() => null),
          api.trades(20).catch(() => []),
        ]);
        setSummary(s);
        setBehavioral(b);
        setTrades(t || []);
      } catch (e: any) {
        setError(e.message || "Failed to load");
        if (e.message === "Unauthorized") router.push("/login");
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0f14]">
        <Nav />
        <p className="p-8 text-slate-400">Loading dashboard…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Welcome{user?.full_name ? `, ${user.full_name}` : ""}
          </h1>
          <p className="text-sm text-slate-400">{user?.email} · Plan: {user?.plan || "free"}</p>
        </div>

        {error && (
          <p className="rounded-lg border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-300">{error}</p>
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Trades", value: summary?.total_trades ?? 0 },
            { label: "Win rate", value: summary ? `${(summary.win_rate * 100).toFixed(0)}%` : "—" },
            { label: "Total PnL", value: summary?.total_pnl?.toFixed?.(2) ?? "—" },
            { label: "Events", value: behavioral?.events?.length ?? 0 },
          ].map((c) => (
            <div key={c.label} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <p className="text-xs uppercase tracking-wide text-slate-500">{c.label}</p>
              <p className="mt-1 text-2xl font-semibold text-white">{c.value}</p>
            </div>
          ))}
        </div>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-300">Behavioral signals</h2>
          <p className="mb-3 text-sm text-slate-400">{behavioral?.message || "Connect a broker or import trades to see signals."}</p>
          <ul className="space-y-2">
            {(behavioral?.events || []).slice(0, 8).map((e: any) => (
              <li key={e.id} className="rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2 text-sm text-slate-300">
                <span className="font-medium text-amber-400">{e.event_type || e.type}</span>
                {e.message ? ` — ${e.message}` : ""}
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-300">Recent trades (from broker data)</h2>
          {trades.length === 0 ? (
            <p className="text-sm text-slate-500">No trades yet. Use Import or connect MT5/IBKR.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-slate-500">
                  <tr>
                    <th className="py-2 pr-4">Symbol</th>
                    <th className="py-2 pr-4">Side</th>
                    <th className="py-2 pr-4">PnL</th>
                    <th className="py-2">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.map((t: any) => (
                    <tr key={t.id} className="border-t border-slate-800 text-slate-300">
                      <td className="py-2 pr-4">{t.symbol}</td>
                      <td className="py-2 pr-4">{t.side}</td>
                      <td className={`py-2 pr-4 ${(t.pnl ?? 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                        {t.pnl ?? "—"}
                      </td>
                      <td className="py-2 text-slate-500">{t.closed_at || t.opened_at || ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
