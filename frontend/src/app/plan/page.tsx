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
  const [symbols, setSymbols] = useState("XAUUSD,EURUSD");
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
          setRiskPct(p.risk_per_trade_pct ?? 1);
          setSymbols((p.allowed_symbols || []).join(",") || "XAUUSD,EURUSD");
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
        max_trades_per_day: maxTrades,
        risk_per_trade_pct: riskPct,
        allowed_symbols: symbols.split(",").map((s) => s.trim()).filter(Boolean),
        is_active: true,
      };
      const saved = plan ? await api.updatePlan(plan.id, body) : await api.createPlan(body);
      setPlan(saved);
      setMsg("Plan saved.");
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
        <h1 className="mb-2 text-2xl font-bold text-white">Trading plan</h1>
        <p className="mb-6 text-sm text-slate-400">Rules the system uses to flag overtrading and plan deviations — from real data, not memory.</p>
        <form onSubmit={save} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <label className="block text-sm text-slate-400">
            Max trades per day
            <input type="number" min={1} value={maxTrades} onChange={(e) => setMaxTrades(+e.target.value)} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
          </label>
          <label className="block text-sm text-slate-400">
            Risk per trade (%)
            <input type="number" step={0.1} min={0.1} value={riskPct} onChange={(e) => setRiskPct(+e.target.value)} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
          </label>
          <label className="block text-sm text-slate-400">
            Allowed symbols (comma-separated)
            <input value={symbols} onChange={(e) => setSymbols(e.target.value)} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white" />
          </label>
          {msg && <p className="text-sm text-slate-300">{msg}</p>}
          <button type="submit" className="w-full rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white">Save plan</button>
        </form>
      </main>
    </div>
  );
}
