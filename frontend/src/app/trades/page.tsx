"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

export default function TradesPage() {
  const router = useRouter();
  const [rows, setRows] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        await api.me();
        const data = await api.tradesWithContext();
        setRows(data.trades || []);
      } catch (e: any) {
        if (e.message === "Unauthorized") router.push("/login");
        else setError(e.message);
      }
    })();
  }, [router]);

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-500">Trades with context</p>
          <h1 className="text-2xl font-bold text-white">Not a journal table</h1>
          <p className="text-sm text-slate-400">Each fill includes behavioral verdict — disciplined or break.</p>
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <ul className="space-y-3">
          {rows.length === 0 && (
            <p className="text-sm text-slate-500">No trades yet. Connections → demo or broker.</p>
          )}
          {rows.map((t) => (
            <li
              key={t.id}
              className={`rounded-2xl border p-4 ${
                t.severity === "red" ? "border-red-900/50 bg-red-950/20" : "border-slate-800 bg-slate-900/50"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-semibold text-white">
                    {t.symbol} <span className="text-sm font-normal text-slate-500">{t.side}</span>
                  </p>
                  <p className="text-xs text-slate-500">
                    {t.entry_time ? new Date(t.entry_time).toLocaleString() : "—"}
                  </p>
                </div>
                <div className="text-right">
                  <p className={`text-lg font-semibold ${(t.net_pnl ?? 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {t.net_pnl != null ? Number(t.net_pnl).toFixed(2) : "—"}
                  </p>
                  <p
                    className={`text-xs font-semibold uppercase tracking-wide ${
                      t.verdict === "BEHAVIORAL BREAK" ? "text-red-400" : "text-green-400"
                    }`}
                  >
                    {t.verdict}
                  </p>
                </div>
              </div>
              <div className="mt-3 grid gap-2 text-xs text-slate-400 sm:grid-cols-3">
                <div className="rounded-lg bg-slate-950/50 px-2 py-1.5">
                  <p className="text-slate-600">Before</p>
                  <p>
                    Risk {t.before?.risk} · Frequency {t.before?.frequency}
                  </p>
                </div>
                <div className="rounded-lg bg-slate-950/50 px-2 py-1.5">
                  <p className="text-slate-600">Gap after prior</p>
                  <p>{t.minutes_after_prev != null ? `${t.minutes_after_prev} min` : "—"}</p>
                </div>
                <div className="rounded-lg bg-slate-950/50 px-2 py-1.5">
                  <p className="text-slate-600">Loss streak before</p>
                  <p>{t.loss_streak_before ?? 0}</p>
                </div>
              </div>
              {t.flags?.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {t.flags.map((f: string) => (
                    <li key={f} className="text-sm text-slate-300">
                      · {f}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
