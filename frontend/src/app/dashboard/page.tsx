"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

function signalColor(status: string) {
  if (status === "red") return "text-red-400 border-red-900/50 bg-red-950/30";
  if (status === "amber") return "text-amber-400 border-amber-900/50 bg-amber-950/30";
  return "text-green-400 border-green-900/40 bg-green-950/20";
}

function stateBanner(color: string) {
  if (color === "red") return "border-red-800 bg-red-950/40 text-red-200";
  if (color === "amber") return "border-amber-800 bg-amber-950/40 text-amber-100";
  return "border-green-800 bg-green-950/30 text-green-100";
}

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);
  const [snap, setSnap] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const me = await api.me();
        setUser(me);
        try {
          const ob = await api.onboardingStatus();
          if (!ob.complete) {
            router.replace("/onboarding");
            return;
          }
        } catch {
          /* ignore */
        }
        const [t, s] = await Promise.all([
          api.tilt().catch(() => null),
          api.summary().catch(() => null),
        ]);
        setSnap(t);
        setSummary(s);
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
        <p className="p-8 text-slate-400">Loading behavioral state…</p>
      </div>
    );
  }

  const tilt = snap?.tilt;
  const baseline = snap?.baseline;
  const autopsy = snap?.autopsy;
  const constitution = snap?.constitution;
  const signals = tilt?.signals ? Object.values(tilt.signals) : [];
  const noticed = signals.find((s: any) => s.status === "red" || s.status === "amber") as any;

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-500">How are you trading?</p>
          <h1 className="mt-1 text-2xl font-bold text-white">
            {user?.full_name ? user.full_name : "Trader"}
          </h1>
          <p className="text-sm text-slate-500">{user?.email}</p>
        </div>

        {error && (
          <p className="rounded-lg border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-300">{error}</p>
        )}

        <div className="flex flex-wrap gap-2">
          {[
            ["/monitor", "Open Monitor"],
            ["/trades", "Trades + verdicts"],
            ["/chat", "Ask Coach"],
            ["/import", "Load data"],
          ].map(([href, label]) => (
            <button
              key={href}
              type="button"
              onClick={() => router.push(href)}
              className="rounded-full border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-blue-600 hover:text-white"
            >
              {label}
            </button>
          ))}
        </div>

        <section className={`rounded-2xl border p-6 ${stateBanner(tilt?.color || "green")}`}>
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide opacity-80">Behavioral state</p>
              <p className="mt-1 text-3xl font-bold tracking-tight">{tilt?.state_label || "—"}</p>
            </div>
            <div className="text-right">
              <p className="text-xs uppercase tracking-wide opacity-80">Tilt score</p>
              <p className="text-4xl font-bold tabular-nums">
                {tilt?.tilt_score ?? "—"}
                <span className="text-lg font-medium opacity-70"> / 100</span>
              </p>
            </div>
          </div>
          {tilt?.do_not_trade && (
            <div className="mt-4 space-y-3 rounded-xl border border-red-700/60 bg-red-950/60 px-4 py-3 text-sm font-medium text-red-100">
              <p>TRADING PAUSED (recommended) — Behavior outside your baseline. Cooldown 30–60 minutes.</p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-lg bg-red-800 px-3 py-1.5 text-xs font-semibold text-white"
                  onClick={async () => {
                    try {
                      const r = await api.acknowledgePause();
                      setError(r.message || "Pause logged");
                    } catch (e: any) {
                      setError(e.message);
                    }
                  }}
                >
                  I will pause
                </button>
                <button
                  type="button"
                  className="rounded-lg border border-red-500/50 px-3 py-1.5 text-xs text-red-200"
                  onClick={async () => {
                    try {
                      const r = await api.overridePause();
                      setError(r.warning || "Override logged");
                    } catch (e: any) {
                      setError(e.message);
                    }
                  }}
                >
                  Override (logged)
                </button>
              </div>
            </div>
          )}
          <p className="mt-4 text-sm leading-relaxed opacity-90">{tilt?.recommendation}</p>
        </section>

        <section className="grid gap-3 sm:grid-cols-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3 text-center">
            <p className="text-xs text-slate-500">Plan adherence</p>
            <p className="text-xl font-bold text-white">
              {autopsy?.plan_adherence_pct != null ? `${autopsy.plan_adherence_pct}%` : "—"}
            </p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3 text-center">
            <p className="text-xs text-slate-500">Deviation</p>
            <p className="text-xl font-bold text-white">{tilt?.tilt_score != null ? `${tilt.tilt_score}` : "—"}</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3 text-center">
            <p className="text-xs text-slate-500">Today trades</p>
            <p className="text-xl font-bold text-white">
              {autopsy?.trades ?? 0}
              {autopsy?.planned_max != null ? (
                <span className="text-sm text-slate-500"> / {autopsy.planned_max}</span>
              ) : null}
            </p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3 text-center">
            <p className="text-xs text-slate-500">Win rate</p>
            <p className="text-xl font-bold text-white">
              {summary?.win_rate != null ? `${(summary.win_rate * 100).toFixed(0)}%` : "—"}
            </p>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
          <h2 className="text-sm font-semibold text-slate-300">What TiltShield noticed</h2>
          <p className="mt-2 text-sm text-slate-300">
            {noticed
              ? `${noticed.label}: ${noticed.detail}`
              : tilt?.tilt_score != null && tilt.tilt_score < 30
                ? "Behavior currently within your normal range."
                : "Connect trades or load demo data to activate live observations."}
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-sm font-semibold text-slate-300">Signals</h2>
          <div className="grid gap-2 sm:grid-cols-2">
            {signals.length === 0 ? (
              <p className="text-sm text-slate-500">Connect trades to activate the Tilt Engine.</p>
            ) : (
              signals.map((s: any) => (
                <div key={s.label} className={`rounded-xl border px-3 py-3 text-sm ${signalColor(s.status)}`}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">{s.label}</span>
                    <span className="text-xs uppercase opacity-80">{s.status}</span>
                  </div>
                  <p className="mt-1 text-xs opacity-90">{s.detail}</p>
                </div>
              ))
            )}
          </div>
        </section>

        <div className="grid gap-4 sm:grid-cols-2">
          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
            <h2 className="text-sm font-semibold text-slate-300">Trading constitution</h2>
            {constitution ? (
              <ul className="mt-3 space-y-1 text-sm text-slate-400">
                <li>
                  Max trades/day: <span className="text-white">{constitution.max_trades_per_day ?? "—"}</span>
                </li>
                <li>
                  Risk/trade:{" "}
                  <span className="text-white">
                    {constitution.max_risk_per_trade ?? constitution.risk_per_trade_pct ?? "—"}%
                  </span>
                </li>
                <li>
                  Symbols:{" "}
                  <span className="text-white">{(constitution.allowed_symbols || []).join(", ") || "—"}</span>
                </li>
              </ul>
            ) : (
              <p className="mt-2 text-sm text-slate-500">
                Set your rules on the{" "}
                <button type="button" className="text-blue-400 underline" onClick={() => router.push("/plan")}>
                  Plan
                </button>{" "}
                page.
              </p>
            )}
          </section>
          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
            <h2 className="text-sm font-semibold text-slate-300">Your baseline</h2>
            {baseline?.ready ? (
              <ul className="mt-3 space-y-1 text-sm text-slate-400">
                <li>~{baseline.trades_per_day_median} trades/day (median)</li>
                <li>
                  {baseline.median_minutes_between_entries != null
                    ? `~${Math.round(baseline.median_minutes_between_entries)} min between entries`
                    : "Pace learning…"}
                </li>
                <li>Symbols: {(baseline.preferred_symbols || []).join(", ") || "—"}</li>
              </ul>
            ) : (
              <p className="mt-2 text-sm text-slate-500">{baseline?.message || "Need more closed trades."}</p>
            )}
          </section>
        </div>

        <p className="text-center text-xs text-slate-600">
          We measure the gap between your constitution and your real trades — not what you meant to do.
        </p>
      </main>
    </div>
  );
}
