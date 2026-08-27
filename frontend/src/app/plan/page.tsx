"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

export default function PlanPage() {
  const router = useRouter();
  const [plan, setPlan] = useState<any>(null);
  const [maxTrades, setMaxTrades] = useState(5);
  const [riskPct, setRiskPct] = useState(1);
  const [maxDailyLoss, setMaxDailyLoss] = useState(3);
  const [symbols, setSymbols] = useState("XAUUSD,EURUSD");
  const [cooldown, setCooldown] = useState(20);
  const [maxLossStreak, setMaxLossStreak] = useState(2);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        await api.me();
        const p = await api.activePlan().catch(() => null);
        if (p) {
          setPlan(p);
          setMaxTrades(p.max_trades_per_day ?? 5);
          setRiskPct(p.max_risk_per_trade ?? 1);
          setMaxDailyLoss(p.max_daily_loss ?? 3);
          setSymbols((p.allowed_symbols || []).join(",") || "XAUUSD,EURUSD");
          const r = p.other_rules || {};
          setCooldown(r.cooldown_minutes_after_loss ?? 20);
          setMaxLossStreak(r.max_consecutive_losses_before_stop ?? 2);
        }
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      const body = {
        name: "Trading Constitution",
        max_trades_per_day: maxTrades,
        max_risk_per_trade: riskPct,
        max_daily_loss: maxDailyLoss,
        allowed_symbols: symbols.split(",").map((s) => s.trim()).filter(Boolean),
        other_rules: {
          cooldown_minutes_after_loss: cooldown,
          max_consecutive_losses_before_stop: maxLossStreak,
          no_risk_increase_after_loss: true,
        },
        active: true,
      };
      const saved = plan ? await api.updatePlan(plan.id, body) : await api.createPlan(body);
      setPlan(saved);
      setMsg("Constitution saved. The Tilt Engine monitors the gap between this and your real trades.");
    } catch (err: any) {
      setMsg(err.message || "Failed to save");
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0f14]">
        <Nav />
        <p className="p-8 text-slate-400">Loading…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-lg px-4 py-8">
        <p className="text-xs uppercase tracking-widest text-slate-500">Trading constitution</p>
        <h1 className="mb-2 text-2xl font-bold text-white">Your rules. We monitor the gap.</h1>
        <p className="mb-6 text-sm text-slate-400">
          A plan is useless if you don&apos;t follow it. These rules feed the Tilt Engine — not a journal.
        </p>
        <form onSubmit={save} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <label className="block text-sm text-slate-400">
            Maximum trades per day
            <input type="number" min={1} value={maxTrades} onChange={(e) => setMaxTrades(+e.target.value)} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
          </label>
          <label className="block text-sm text-slate-400">
            Max risk per trade (%)
            <input type="number" step={0.1} min={0.1} value={riskPct} onChange={(e) => setRiskPct(+e.target.value)} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
          </label>
          <label className="block text-sm text-slate-400">
            Max daily loss (%)
            <input type="number" step={0.1} min={0.1} value={maxDailyLoss} onChange={(e) => setMaxDailyLoss(+e.target.value)} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
          </label>
          <label className="block text-sm text-slate-400">
            Allowed symbols (comma-separated)
            <input value={symbols} onChange={(e) => setSymbols(e.target.value)} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
          </label>
          <label className="block text-sm text-slate-400">
            After a loss: cooldown (minutes)
            <input type="number" min={0} value={cooldown} onChange={(e) => setCooldown(+e.target.value)} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
          </label>
          <label className="block text-sm text-slate-400">
            After N consecutive losses: stop for the session
            <input type="number" min={1} value={maxLossStreak} onChange={(e) => setMaxLossStreak(+e.target.value)} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
          </label>
          <p className="text-xs text-slate-500">Hard rule stored: do not increase risk to recover losses.</p>
          {msg && <p className="text-sm text-slate-300">{msg}</p>}
          <button type="submit" className="w-full rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white">
            Save constitution
          </button>
        </form>
      </main>
    </div>
  );
}
