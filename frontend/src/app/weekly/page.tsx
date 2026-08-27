"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

export default function WeeklyPage() {
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        await api.me();
        const w = await api.weekly();
        setData(w);
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0f14]">
        <Nav />
        <p className="p-8 text-slate-400">Loading weekly behavior…</p>
      </div>
    );
  }

  const week = data?.weekly;
  const cost = data?.cost_of_behavior;
  const tilt = data?.tilt;

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-lg space-y-6 px-4 py-8">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-500">Weekly behavioral report</p>
          <h1 className="text-2xl font-bold text-white">Behavior is the headline</h1>
          <p className="mt-1 text-sm text-slate-400">P&amp;L is secondary. Patterns that cost money come first.</p>
        </div>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <p className="text-sm text-slate-300">{week?.message || "No activity this week yet."}</p>
          <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-xs text-slate-500">Trades</p>
              <p className="text-xl font-semibold text-white">{week?.trades ?? 0}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">P&amp;L</p>
              <p className={`text-xl font-semibold ${(week?.pnl ?? 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                {week?.pnl ?? "—"}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Revenge flags</p>
              <p className="text-xl font-semibold text-amber-400">{week?.revenge_flags ?? 0}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Overtrading flags</p>
              <p className="text-xl font-semibold text-amber-400">{week?.overtrading_flags ?? 0}</p>
            </div>
          </div>
          <p className="mt-4 text-sm text-amber-300/90">Biggest leak: {week?.biggest_behavioral_leak || "—"}</p>
        </section>

        {cost && (
          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="text-sm font-semibold text-slate-300">Cost of behavior (30d estimate)</h2>
            <p className={`mt-2 text-3xl font-bold ${(cost.estimated_behavioral_leakage ?? 0) <= 0 ? "text-red-400" : "text-green-400"}`}>
              {cost.estimated_behavioral_leakage}
            </p>
            <p className="mt-2 text-xs text-slate-500">{cost.note}</p>
          </section>
        )}

        {tilt && (
          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="text-sm font-semibold text-slate-300">Current tilt</h2>
            <p className="mt-2 text-2xl font-bold text-white">
              {tilt.tilt_score}/100 <span className="text-base font-medium text-slate-400">{tilt.state_label}</span>
            </p>
            <p className="mt-2 text-sm text-slate-400">{tilt.recommendation}</p>
          </section>
        )}
      </main>
    </div>
  );
}
