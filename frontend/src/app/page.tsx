"use client";

import Link from "next/link";
import { useState } from "react";

export default function MarketingHome() {
  const [open, setOpen] = useState<"products" | "solutions" | "resources" | null>(null);

  return (
    <div className="min-h-screen bg-[#070a0f] text-slate-100">
      <header className="sticky top-0 z-50 border-b border-slate-800/60 bg-[#070a0f]/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4">
          <Link href="/" className="text-lg font-bold tracking-tight text-white">
            TiltShield
          </Link>

          <nav className="hidden items-center gap-6 text-sm text-slate-400 lg:flex">
            <div
              className="relative"
              onMouseEnter={() => setOpen("products")}
              onMouseLeave={() => setOpen(null)}
            >
              <button type="button" className="hover:text-white">
                Products
              </button>
              {open === "products" && (
                <div className="absolute left-0 top-full z-50 min-w-[200px] rounded-xl border border-slate-800 bg-slate-950 py-2 shadow-xl">
                  <Link href="/#monitor" className="block px-4 py-2 hover:bg-slate-900 hover:text-white">
                    Behavioral Monitor
                  </Link>
                  <Link href="/#plan" className="block px-4 py-2 hover:bg-slate-900 hover:text-white">
                    Trading Plan
                  </Link>
                  <Link href="/#coach" className="block px-4 py-2 hover:bg-slate-900 hover:text-white">
                    AI Coach
                  </Link>
                  <Link href="/#analytics" className="block px-4 py-2 hover:bg-slate-900 hover:text-white">
                    Analytics
                  </Link>
                </div>
              )}
            </div>

            <div
              className="relative"
              onMouseEnter={() => setOpen("solutions")}
              onMouseLeave={() => setOpen(null)}
            >
              <button type="button" className="hover:text-white">
                Solutions
              </button>
              {open === "solutions" && (
                <div className="absolute left-0 top-full z-50 min-w-[200px] rounded-xl border border-slate-800 bg-slate-950 py-2 shadow-xl">
                  <Link href="/#individuals" className="block px-4 py-2 hover:bg-slate-900 hover:text-white">
                    Individual Traders
                  </Link>
                  <Link href="/#prop" className="block px-4 py-2 hover:bg-slate-900 hover:text-white">
                    Prop Traders
                  </Link>
                  <Link href="/#coaches" className="block px-4 py-2 hover:bg-slate-900 hover:text-white">
                    Coaches
                  </Link>
                  <Link href="/#prop" className="block px-4 py-2 hover:bg-slate-900 hover:text-white">
                    Prop Firms
                  </Link>
                </div>
              )}
            </div>

            <div
              className="relative"
              onMouseEnter={() => setOpen("resources")}
              onMouseLeave={() => setOpen(null)}
            >
              <button type="button" className="hover:text-white">
                Resources
              </button>
              {open === "resources" && (
                <div className="absolute left-0 top-full z-50 min-w-[200px] rounded-xl border border-slate-800 bg-slate-950 py-2 shadow-xl">
                  <Link href="/#resources" className="block px-4 py-2 hover:bg-slate-900 hover:text-white">
                    Trading Psychology
                  </Link>
                  <Link href="/#resources" className="block px-4 py-2 hover:bg-slate-900 hover:text-white">
                    Behavioral Risk
                  </Link>
                  <Link href="/#system" className="block px-4 py-2 hover:bg-slate-900 hover:text-white">
                    Guides
                  </Link>
                </div>
              )}
            </div>

            <Link href="/billing" className="hover:text-white">
              Pricing
            </Link>
            <Link href="/login" className="hover:text-white">
              Sign In
            </Link>
            <Link
              href="/login"
              className="rounded-lg bg-blue-600 px-3 py-1.5 font-medium text-white hover:bg-blue-500"
            >
              Start Free
            </Link>
          </nav>

          <div className="flex items-center gap-3 lg:hidden">
            <Link href="/login" className="text-sm text-slate-400">
              Sign In
            </Link>
            <Link href="/login" className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white">
              Start Free
            </Link>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-3xl px-4 pb-16 pt-14 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-400">
          Behavioral risk management
        </p>
        <h1 className="mt-4 text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl">
          Your trading strategy isn&apos;t the problem.
          <span className="mt-2 block text-slate-400">What happens when you stop following it is.</span>
        </h1>
        <p className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-slate-400">
          TiltShield monitors your trading behavior in real time, detects deviations from your normal, and helps
          you intervene before impulsive decisions compound.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link href="/login" className="rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white">
            Start monitoring free
          </Link>
          <span className="text-xs text-slate-500">Connect MT5, IBKR, cTrader, TradingView…</span>
        </div>
      </section>

      <section id="monitor" className="mx-auto max-w-lg px-4 pb-20">
        <div className="rounded-2xl border border-red-900/50 bg-gradient-to-b from-red-950/40 to-slate-950 p-6">
          <p className="text-xs uppercase tracking-widest text-red-300/80">Your behavioral state</p>
          <div className="mt-3 flex items-end justify-between">
            <div>
              <p className="text-sm text-slate-400">Tilt score</p>
              <p className="text-5xl font-bold tabular-nums text-red-300">78</p>
            </div>
            <p className="rounded-full border border-red-700/60 bg-red-950/60 px-3 py-1 text-sm font-semibold text-red-200">
              HIGH RISK
            </p>
          </div>
          <p className="mt-4 text-sm text-red-100/90">
            Your trading behavior has significantly deviated from your baseline.
          </p>
          <ul className="mt-4 space-y-2 text-sm">
            {["Overtrading", "Risk escalation", "Revenge pattern", "Plan adherence"].map((label) => (
              <li key={label} className="flex justify-between border-b border-white/5 py-1.5">
                <span className="text-slate-300">{label}</span>
                <span className="text-red-400">●</span>
              </li>
            ))}
          </ul>
          <p className="mt-5 rounded-xl border border-red-800/40 bg-red-950/50 px-3 py-2 text-sm text-red-100">
            Recommended action: Step away for 30 minutes.
          </p>
        </div>
      </section>

      <section className="border-y border-slate-800/80 bg-slate-950/50 py-16">
        <div className="mx-auto max-w-3xl px-4">
          <h2 className="text-center text-2xl font-bold text-white">
            Your P&amp;L tells you what happened.
            <span className="mt-1 block text-slate-400">TiltShield tells you why.</span>
          </h2>
          <div className="mx-auto mt-10 max-w-md space-y-3 text-sm">
            {[
              ["Trade 1", "+1.2R", "Normal", false],
              ["Trade 2", "−1R", "Normal", false],
              ["Trade 3", "−1R", "Normal", false],
              ["Trade 4", "−2R", "Risk increased", true],
              ["Trade 5", "−1.5R", "Entered 3 min later", true],
            ].map(([t, r, note, bad]) => (
              <div
                key={t as string}
                className={`flex justify-between rounded-xl border px-4 py-3 ${
                  bad ? "border-red-900/50 bg-red-950/20" : "border-slate-800 bg-slate-900/40"
                }`}
              >
                <span className="text-slate-400">{t}</span>
                <span className="font-mono text-slate-200">{r}</span>
                <span className={bad ? "text-red-400" : "text-slate-500"}>{note}</span>
              </div>
            ))}
            <div className="rounded-xl border border-red-700/50 bg-red-950/40 p-4 text-red-100">
              <p className="font-semibold">BEHAVIORAL BREAK</p>
              <p className="mt-2 text-sm opacity-90">Risk increased 2.1× after consecutive losses.</p>
              <p className="mt-1 text-sm opacity-90">Last three entries 4× faster than your normal pace.</p>
            </div>
          </div>
        </div>
      </section>

      <section id="system" className="mx-auto max-w-3xl px-4 py-16">
        <h2 className="text-center text-2xl font-bold text-white">A system — not a journal</h2>
        <p className="mt-2 text-center text-sm text-slate-400">Observe → Detect → Explain → Intervene → Learn</p>
        <ol className="mt-10 space-y-4">
          {[
            ["01 — Observe", "Trading activity from MT5 / IBKR / cTrader / CSV."],
            ["02 — Detect", "Deviations from your personal baseline."],
            ["03 — Explain", "Revenge, overtrading, size-up after loss."],
            ["04 — Intervene", "Pause, soft lock, logged override."],
            ["05 — Learn", "Patterns that repeatedly affect performance."],
          ].map(([title, body]) => (
            <li key={title} className="rounded-xl border border-slate-800 bg-slate-900/40 px-5 py-4">
              <p className="font-semibold text-blue-300">{title}</p>
              <p className="mt-1 text-sm text-slate-400">{body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section id="plan" className="border-t border-slate-800 bg-slate-950/40 py-14">
        <div className="mx-auto max-w-3xl px-4 text-center">
          <h2 className="text-xl font-bold text-white">Trading Plan (Constitution)</h2>
          <p className="mt-2 text-sm text-slate-400">
            Max trades, risk %, cooldown after losses, allowed symbols. Measured against real fills.
          </p>
        </div>
      </section>
      <section id="coach" className="py-14">
        <div className="mx-auto max-w-3xl px-4 text-center">
          <h2 className="text-xl font-bold text-white">AI Coach</h2>
          <p className="mt-2 text-sm text-slate-400">
            Opens with your tilt and patterns — evidence-based, not motivational slogans.
          </p>
        </div>
      </section>
      <section id="analytics" className="border-y border-slate-800 bg-slate-950/40 py-14">
        <div className="mx-auto max-w-3xl px-4 text-center">
          <h2 className="text-xl font-bold text-white">Analytics that matter</h2>
          <p className="mt-2 text-sm text-slate-400">
            Patterns, weekly reports, cost-of-behavior — not 100 vanity charts.
          </p>
        </div>
      </section>

      <section id="individuals" className="mx-auto max-w-3xl px-4 py-12">
        <h2 className="text-center text-xl font-bold text-white">Built for</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-slate-800 p-5">
            <p className="font-semibold text-white">Individual traders</p>
            <p className="mt-1 text-sm text-slate-400">Know your normal. Know when you break it. Know what to do next.</p>
          </div>
          <div id="prop" className="rounded-xl border border-slate-800 p-5">
            <p className="font-semibold text-white">Prop traders &amp; firms</p>
            <p className="mt-1 text-sm text-slate-400">Desk heatmap: who is elevated or high-risk right now.</p>
          </div>
          <div id="coaches" className="rounded-xl border border-slate-800 p-5 sm:col-span-2">
            <p className="font-semibold text-white">Coaches</p>
            <p className="mt-1 text-sm text-slate-400">Review clients against constitution and tilt — pause logs included.</p>
          </div>
        </div>
      </section>

      <section id="resources" className="border-t border-slate-800 py-12">
        <div className="mx-auto max-w-3xl px-4 text-center text-sm text-slate-500">
          <p className="font-medium text-slate-400">Resources</p>
          <p className="mt-2">Trading psychology · Behavioral risk · Guides</p>
        </div>
      </section>

      <section className="mx-auto max-w-xl px-4 py-16 text-center">
        <h2 className="text-2xl font-bold text-white">Not the market. You.</h2>
        <p className="mt-2 text-slate-400">TiltShield watches the part of trading most platforms ignore.</p>
        <Link href="/login" className="mt-8 inline-block rounded-xl bg-blue-600 px-8 py-3 text-sm font-semibold text-white">
          Start Free
        </Link>
      </section>

      <footer className="border-t border-slate-800 py-10">
        <div className="mx-auto flex max-w-6xl flex-wrap justify-between gap-6 px-4 text-xs text-slate-600">
          <span>TiltShield</span>
          <div className="flex flex-wrap gap-4">
            <Link href="/#monitor" className="hover:text-slate-400">
              Products
            </Link>
            <Link href="/#prop" className="hover:text-slate-400">
              Solutions
            </Link>
            <Link href="/billing" className="hover:text-slate-400">
              Pricing
            </Link>
            <Link href="/login" className="hover:text-slate-400">
              Sign In
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
