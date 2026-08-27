"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

const API_HOST = (process.env.NEXT_PUBLIC_API_URL || "https://trading-therapist-production.up.railway.app").replace(/\/$/, "").replace(/\/api\/v1$/, "");
const MT5_WEBHOOK = `${API_HOST}/api/v1/connectors/mt5/webhook`;

export default function ImportPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState("");
  const [copied, setCopied] = useState("");

  useEffect(() => {
    api.me().catch(() => router.push("/login"));
  }, [router]);

  function copy(text: string, label: string) {
    navigator.clipboard?.writeText(text).then(() => {
      setCopied(label);
      setTimeout(() => setCopied(""), 2000);
    });
  }

  async function connectMt5() {
    setError("");
    try {
      const res = await api.connectBroker("mt5");
      setToken(res.api_token || "");
    } catch (e: any) {
      setError(e.message || "Failed to connect");
    }
  }

  async function upload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await api.uploadFlexCsv(file);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-2xl space-y-8 px-4 py-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Import real trades</h1>
          <p className="mt-1 text-sm text-slate-400">
            No manual journaling. Data comes from your broker so you cannot rewrite history.
          </p>
        </div>

        {/* MT5 */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="mb-1 text-lg font-semibold text-white">1. MetaTrader 5 (automatic)</h2>
          <p className="mb-4 text-sm text-slate-400">
            EA posts every closed deal to our webhook. Behavioral signals update automatically.
          </p>

          <div className="mb-4 space-y-2">
            <p className="text-xs uppercase tracking-wide text-slate-500">Webhook URL (paste into EA)</p>
            <div className="flex gap-2">
              <code className="flex-1 break-all rounded-lg bg-slate-950 px-3 py-2 text-xs text-blue-300">{MT5_WEBHOOK}</code>
              <button type="button" onClick={() => copy(MT5_WEBHOOK, "url")} className="rounded-lg border border-slate-700 px-3 text-xs text-slate-300">
                {copied === "url" ? "Copied" : "Copy"}
              </button>
            </div>
          </div>

          <button type="button" onClick={connectMt5} className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white">
            Generate API token
          </button>

          {token && (
            <div className="mt-4 space-y-2">
              <p className="text-xs uppercase tracking-wide text-slate-500">API token (paste into EA · shown once)</p>
              <div className="flex gap-2">
                <code className="flex-1 break-all rounded-lg bg-slate-950 px-3 py-2 text-xs text-green-400">{token}</code>
                <button type="button" onClick={() => copy(token, "token")} className="rounded-lg border border-slate-700 px-3 text-xs text-slate-300">
                  {copied === "token" ? "Copied" : "Copy"}
                </button>
              </div>
            </div>
          )}

          <ol className="mt-5 list-decimal space-y-1 pl-5 text-sm text-slate-400">
            <li>Copy <code className="text-slate-300">scripts/TradingTherapistEA.mq5</code> from the GitHub repo into MT5 → MQL5/Experts</li>
            <li>Compile in MetaEditor (F7)</li>
            <li>Tools → Options → Expert Advisors → Allow WebRequest → add <code className="text-slate-300">{API_HOST}</code></li>
            <li>Attach EA to any chart · set WebhookURL + ApiKey (token above)</li>
            <li>Close a trade → it appears on Dashboard</li>
          </ol>
        </section>

        {/* IBKR */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="mb-1 text-lg font-semibold text-white">2. Interactive Brokers (Flex CSV)</h2>
          <p className="mb-4 text-sm text-slate-400">
            Export a Flex Query CSV of closed trades and upload it here. Duplicates are skipped.
          </p>
          <form onSubmit={upload} className="space-y-4">
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full text-sm text-slate-300"
            />
            <button type="submit" disabled={!file || loading} className="w-full rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white disabled:opacity-40">
              {loading ? "Uploading…" : "Upload Flex CSV"}
            </button>
          </form>
          {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
          {result && (
            <div className="mt-3 rounded-lg border border-green-900/40 bg-green-950/30 p-3 text-sm text-green-300">
              Parsed {result.parsed} · Created {result.created} · Skipped {result.skipped_duplicates} · Events {result.behavioral_events_created}
            </div>
          )}
        </section>

        <p className="text-center text-xs text-slate-600">
          After data lands, open Dashboard for stats and Therapist for coaching grounded in those trades.
        </p>
      </main>
    </div>
  );
}
