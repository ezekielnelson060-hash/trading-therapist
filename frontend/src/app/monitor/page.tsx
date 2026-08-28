"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

export default function MonitorPage() {
  const router = useRouter();
  const [snap, setSnap] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [trades, setTrades] = useState<any[]>([]);

  useEffect(() => {
    (async () => {
      try {
        await api.me();
        const [t, e, tr] = await Promise.all([
          api.tilt().catch(() => null),
          api.events().catch(() => []),
          api.trades(20).catch(() => []),
        ]);
        setSnap(t);
        setEvents(e || []);
        setTrades(tr || []);
      } catch {
        router.push("/login");
      }
    })();
  }, [router]);

  const tilt = snap?.tilt;
  const signals = tilt?.signals ? Object.values(tilt.signals) : [];

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-500">Live behavior monitor</p>
          <h1 className="text-2xl font-bold text-white">Cockpit</h1>
          <p className="text-sm text-slate-400">Something is watching your behavior for you.</p>
        </div>

        <section
          className={`rounded-2xl border p-6 ${
            tilt?.color === "red"
              ? "border-red-800 bg-red-950/30 text-red-100"
              : tilt?.color === "amber"
                ? "border-amber-800 bg-amber-950/30 text-amber-100"
                : "border-green-800 bg-green-950/20 text-green-100"
          }`}
        >
          <p className="text-xs uppercase opacity-80">Current state</p>
          <div className="mt-1 flex items-end justify-between">
            <p className="text-3xl font-bold">{tilt?.state_label || "—"}</p>
            <p className="text-4xl font-bold tabular-nums">
              {tilt?.tilt_score ?? "—"}
              <span className="text-lg opacity-70"> / 100</span>
            </p>
          </div>
          <p className="mt-3 text-sm opacity-90">{tilt?.recommendation}</p>
        </section>

        <section>
          <h2 className="mb-3 text-sm font-semibold text-slate-300">Behavioral signals</h2>
          <div className="overflow-hidden rounded-xl border border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/80 text-xs text-slate-500">
                <tr>
                  <th className="px-3 py-2">Signal</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Detail</th>
                </tr>
              </thead>
              <tbody>
                {signals.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-3 py-4 text-slate-500">
                      Connect trades to activate signals.
                    </td>
                  </tr>
                )}
                {signals.map((s: any) => (
                  <tr key={s.label} className="border-t border-slate-800">
                    <td className="px-3 py-2 text-slate-200">{s.label}</td>
                    <td className="px-3 py-2">
                      <span className={s.status === "red" ? "text-red-400" : s.status === "amber" ? "text-amber-400" : "text-green-400"}>
                        {s.status}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-slate-500">{s.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-sm font-semibold text-slate-300">Timeline</h2>
          <ul className="space-y-2">
            {events.slice(0, 12).map((e) => (
              <li key={e.id} className="rounded-lg border border-slate-800 bg-slate-900/40 px-3 py-2 text-sm">
                <span className="text-slate-500">{e.detected_at ? new Date(e.detected_at).toLocaleString() : "—"}</span>
                <span className="mx-2 text-slate-600">·</span>
                <span className="text-slate-200">{e.title || e.type}</span>
              </li>
            ))}
            {trades.slice(0, 8).map((t) => (
              <li key={t.id} className="rounded-lg border border-slate-800/60 px-3 py-2 text-sm text-slate-400">
                {t.closed_at || t.opened_at ? new Date(t.closed_at || t.opened_at).toLocaleString() : "—"} — {t.symbol}{" "}
                <span className={(t.pnl || 0) >= 0 ? "text-green-400" : "text-red-400"}>
                  {t.pnl != null ? Number(t.pnl).toFixed(2) : "—"}
                </span>
              </li>
            ))}
            {events.length === 0 && trades.length === 0 && (
              <p className="text-sm text-slate-500">No timeline yet. Load demo data or connect a broker.</p>
            )}
          </ul>
        </section>
      </main>
    </div>
  );
}
