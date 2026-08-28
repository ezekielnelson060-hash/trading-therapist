"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

export default function WeeklyPage() {
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        await api.me();
        setData(await api.weekly());
      } catch (e: any) {
        if (e.message === "Unauthorized") router.push("/login");
        else setError(e.message);
      }
    })();
  }, [router]);

  const week = data?.weekly;
  const cost = data?.cost_of_behavior;
  const tilt = data?.tilt;

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-500">Reports</p>
          <h1 className="text-2xl font-bold text-white">Your week in behavior</h1>
          <p className="text-sm text-slate-400">P&amp;L is secondary. Behavior is the headline.</p>
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
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

        <div className="grid gap-4 sm:grid-cols-2">
          <section className="rounded-2xl border border-green-900/30 bg-green-950/10 p-5">
            <h2 className="text-sm font-semibold text-green-300">Improved / stable</h2>
            <ul className="mt-2 space-y-1 text-sm text-slate-300">
              {(week?.improved || ["Keep following your constitution"]).map((x: string) => (
                <li key={x}>· {x}</li>
              ))}
            </ul>
          </section>
          <section className="rounded-2xl border border-amber-900/40 bg-amber-950/15 p-5">
            <h2 className="text-sm font-semibold text-amber-300">Needs attention</h2>
            <ul className="mt-2 space-y-1 text-sm text-slate-300">
              {(week?.needs_attention || ["No major flags this week"]).map((x: string) => (
                <li key={x}>· {x}</li>
              ))}
            </ul>
          </section>
        </div>

        {week?.focus_next_week && (
          <section className="rounded-2xl border border-blue-900/40 bg-blue-950/20 p-5">
            <h2 className="text-sm font-semibold text-blue-300">Your focus for next week</h2>
            <p className="mt-2 text-sm text-slate-200">{week.focus_next_week}</p>
          </section>
        )}

        {cost && (
          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="text-sm font-semibold text-slate-300">Cost of behavior (estimate)</h2>
            <p
              className={`mt-2 text-3xl font-bold ${
                (cost.estimated_behavioral_leakage ?? 0) <= 0 ? "text-red-400" : "text-green-400"
              }`}
            >
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
