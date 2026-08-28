"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const MARKETS = ["Forex", "Futures", "Stocks", "Crypto", "Options"];
const STYLES = ["Day trading", "Swing trading", "Scalping", "Prop trading"];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [market, setMarket] = useState("Forex");
  const [style, setStyle] = useState("Day trading");
  const [maxTrades, setMaxTrades] = useState(5);
  const [risk, setRisk] = useState(1);
  const [cooldown, setCooldown] = useState(30);
  const [symbols, setSymbols] = useState("EURUSD, XAUUSD");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [building, setBuilding] = useState(false);
  const [checks, setChecks] = useState([false, false, false, false, false]);

  useEffect(() => {
    (async () => {
      try {
        await api.me();
        const s = await api.onboardingStatus();
        if (s.complete) router.replace("/dashboard");
      } catch {
        router.replace("/login");
      }
    })();
  }, [router]);

  async function saveStep1() {
    setBusy(true);
    try {
      await api.saveOnboarding({ market_type: market, trading_style: style });
      setStep(2);
    } catch (e: any) {
      setMsg(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function saveStep2() {
    setBusy(true);
    try {
      await api.saveOnboarding({
        market_type: market,
        trading_style: style,
        max_trades_per_day: maxTrades,
        max_risk_per_trade: risk,
        cooldown_after_losses: cooldown,
        symbols: symbols.split(/[, ]+/).filter(Boolean),
      });
      setStep(3);
    } catch (e: any) {
      setMsg(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function finish() {
    setStep(4);
    setBuilding(true);
    for (let i = 0; i < 5; i++) {
      await new Promise((r) => setTimeout(r, 450));
      setChecks((c) => c.map((v, idx) => (idx <= i ? true : v)));
    }
    try {
      await api.saveOnboarding({ complete: true });
    } catch {
      /* continue */
    }
    setBuilding(false);
  }

  return (
    <div className="min-h-screen bg-[#070a0f] px-4 py-10 text-slate-100">
      <div className="mx-auto max-w-lg">
        <p className="text-xs uppercase tracking-widest text-blue-400">TiltShield onboarding</p>
        <div className="mt-2 flex gap-1">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className={`h-1 flex-1 rounded ${step >= n ? "bg-blue-500" : "bg-slate-800"}`} />
          ))}
        </div>
        {msg && <p className="mt-4 text-sm text-red-400">{msg}</p>}

        {step === 1 && (
          <div className="mt-8 space-y-6">
            <h1 className="text-2xl font-bold text-white">What do you trade?</h1>
            <p className="text-sm text-slate-400">Let&apos;s understand your trading environment.</p>
            <div>
              <p className="mb-2 text-sm text-slate-300">Market</p>
              <div className="grid grid-cols-2 gap-2">
                {MARKETS.map((m) => (
                  <button key={m} type="button" onClick={() => setMarket(m)} className={`rounded-xl border px-3 py-2.5 text-sm ${market === m ? "border-blue-500 bg-blue-950/40 text-white" : "border-slate-800 text-slate-400"}`}>{m}</button>
                ))}
              </div>
            </div>
            <div>
              <p className="mb-2 text-sm text-slate-300">Trading style</p>
              <div className="grid grid-cols-2 gap-2">
                {STYLES.map((s) => (
                  <button key={s} type="button" onClick={() => setStyle(s)} className={`rounded-xl border px-3 py-2.5 text-sm ${style === s ? "border-blue-500 bg-blue-950/40 text-white" : "border-slate-800 text-slate-400"}`}>{s}</button>
                ))}
              </div>
            </div>
            <button type="button" disabled={busy} onClick={saveStep1} className="w-full rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white">Continue</button>
          </div>
        )}

        {step === 2 && (
          <div className="mt-8 space-y-5">
            <h1 className="text-2xl font-bold text-white">Define your rules</h1>
            <p className="text-sm text-slate-400">What does disciplined trading look like for you?</p>
            <label className="block text-sm"><span className="text-slate-400">Maximum trades / day</span>
              <input type="number" value={maxTrades} onChange={(e) => setMaxTrades(Number(e.target.value))} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
            </label>
            <label className="block text-sm"><span className="text-slate-400">Maximum risk / trade (%)</span>
              <input type="number" step="0.1" value={risk} onChange={(e) => setRisk(Number(e.target.value))} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
            </label>
            <label className="block text-sm"><span className="text-slate-400">After consecutive losses — break (minutes)</span>
              <input type="number" value={cooldown} onChange={(e) => setCooldown(Number(e.target.value))} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
            </label>
            <label className="block text-sm"><span className="text-slate-400">Symbols (comma-separated)</span>
              <input value={symbols} onChange={(e) => setSymbols(e.target.value)} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
            </label>
            <button type="button" disabled={busy} onClick={saveStep2} className="w-full rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white">Create my trading rules</button>
          </div>
        )}

        {step === 3 && (
          <div className="mt-8 space-y-5">
            <h1 className="text-2xl font-bold text-white">Connect your trading</h1>
            <p className="text-sm text-slate-400">We establish your baseline from real activity. Tokens stay under the hood.</p>
            <button type="button" onClick={() => router.push("/import")} className="w-full rounded-xl border border-slate-700 bg-slate-900/60 px-4 py-4 text-left">
              <p className="font-medium text-white">MetaTrader 5</p>
              <p className="text-xs text-slate-500">Automatic monitoring</p>
            </button>
            <button type="button" onClick={() => router.push("/import")} className="w-full rounded-xl border border-slate-700 bg-slate-900/60 px-4 py-4 text-left">
              <p className="font-medium text-white">Interactive Brokers</p>
              <p className="text-xs text-slate-500">Flex CSV / sync</p>
            </button>
            <button type="button" onClick={async () => { try { await api.demoSeed(); setMsg("Demo sequence loaded"); } catch (e: any) { setMsg(e.message); } }} className="w-full rounded-xl border border-amber-900/50 bg-amber-950/20 px-4 py-4 text-left">
              <p className="font-medium text-amber-100">Load demo behavior sequence</p>
              <p className="text-xs text-amber-200/60">See tilt without a live broker</p>
            </button>
            <button type="button" onClick={finish} className="w-full rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white">Continue to baseline</button>
          </div>
        )}

        {step === 4 && (
          <div className="mt-8 space-y-4">
            <h1 className="text-2xl font-bold text-white">{building ? "Building your behavioral baseline…" : "Your baseline is ready"}</h1>
            <ul className="space-y-2 text-sm">
              {["Analyzing trading frequency", "Calculating risk patterns", "Mapping trading sessions", "Detecting repeated behaviors", "Establishing your normal"].map((label, i) => (
                <li key={label} className="flex items-center gap-2 text-slate-300">
                  <span className={checks[i] ? "text-green-400" : "text-slate-600"}>{checks[i] ? "✓" : "○"}</span>
                  {label}
                </li>
              ))}
            </ul>
            {!building && (
              <button type="button" onClick={() => router.replace("/dashboard")} className="mt-4 w-full rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white">
                See my trading profile →
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
