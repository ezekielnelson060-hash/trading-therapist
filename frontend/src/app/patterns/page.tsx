"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

export default function PatternsPage() {
  const router = useRouter();
  const [snap, setSnap] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [weekly, setWeekly] = useState<any>(null);

  useEffect(() => {
    (async () => {
      try {
        await api.me();
        const [t, e, w] = await Promise.all([
          api.tilt().catch(() => null),
          api.events().catch(() => []),
          api.weekly().catch(() => null),
        ]);
        setSnap(t);
        setEvents(e || []);
        setWeekly(w);
      } catch {
        router.push("/login");
      }
    })();
  }, [router]);

  const patterns = useMemo(() => {
    const signals = snap?.tilt?.signals || {};
    const cost = snap?.cost_of_behavior || weekly?.cost_of_behavior;
    return { signals, cost };
  }, [snap, weekly]);

  const revenge = events.filter((e) => /revenge|pause|tilt/i.test(String(e.type) + String(e.title))).length;
  const overtrade = events.filter((e) => /overtrade|frequency|pace/i.test(String(e.type) + String(e.title))).length;

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-500">Your behavioral patterns</p>
          <h1 className="text-2xl font-bold text-white">Patterns</h1>
          <p className="text-sm text-slate-400">Learning the individual — not a generic analytics suite.</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <article className="rounded-2xl border border-red-900/40 bg-red-950/20 p-5">
            <p className="text-xs uppercase text-red-400">Revenge-style pressure</p>
            <p className="mt-1 text-2xl font-bold text-white">{revenge || "—"} detections</p>
            <p className="mt-2 text-sm text-slate-400">Typical trigger: consecutive losses. Response: faster re-entry.</p>
          </article>
          <article className="rounded-2xl border border-amber-900/40 bg-amber-950/20 p-5">
            <p className="text-xs uppercase text-amber-400">Overtrading pressure</p>
            <p className="mt-1 text-2xl font-bold text-white">{overtrade || "—"} detections</p>
            <p className="mt-2 text-sm text-slate-400">Typical trigger: session heat. Response: higher frequency.</p>
          </article>
        </div>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5">
          <h2 className="text-sm font-semibold text-slate-300">Live signal map</h2>
          <ul className="mt-3 space-y-2">
            {Object.values(patterns.signals || {}).length === 0 && (
              <li className="text-sm text-slate-500">Need closed trades for pattern scoring.</li>
            )}
            {Object.values(patterns.signals || {}).map((s: any) => (
              <li key={s.label} className="flex justify-between text-sm">
                <span className="text-slate-300">{s.label}</span>
                <span className={s.status === "red" ? "text-red-400" : s.status === "amber" ? "text-amber-400" : "text-green-400"}>
                  {s.status}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <p className="text-xs text-slate-600">
          Cost figures elsewhere are counterfactual estimates — not return predictions.
        </p>
      </main>
    </div>
  );
}
