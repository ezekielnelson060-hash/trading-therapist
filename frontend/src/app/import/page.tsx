"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

const BROKERS = [
  { id: "mt5", name: "MetaTrader 5", method: "Webhook token" },
  { id: "ibkr", name: "Interactive Brokers", method: "Flex CSV / webhook" },
  { id: "ctrader", name: "cTrader", method: "Webhook" },
  { id: "tradingview", name: "TradingView", method: "Alert webhook" },
  { id: "ninjatrader", name: "NinjaTrader", method: "Webhook" },
  { id: "csv", name: "Any broker (CSV)", method: "Upload" },
];

export default function ImportPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [accountId, setAccountId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<"ibkr" | "csv">("ibkr");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [tokenInfo, setTokenInfo] = useState<any>(null);
  const [connections, setConnections] = useState<any[]>([]);

  useEffect(() => {
    (async () => {
      if (!localStorage.getItem("tt_token")) {
        router.replace("/login");
        return;
      }
      try {
        setConnections(await api.brokers());
      } catch {
        /* ignore */
      }
    })();
  }, [router]);

  async function connect(broker: string) {
    setError("");
    try {
      const r = await api.connectBroker(broker, accountId || broker);
      setTokenInfo(r);
      setConnections(await api.brokers());
      setResult({ note: `Connected ${broker}. Use api_token on webhooks as X-API-Key.` });
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function upload() {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res =
        mode === "ibkr"
          ? await api.uploadFlexCsv(file, accountId || "flex")
          : await api.uploadGenericCsv(file, "csv");
      setResult(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-2xl space-y-6 px-4 py-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Connections</h1>
          <p className="mt-1 text-sm text-slate-400">
            Connect your account. Tokens stay under the hood — all feeds hit the same tilt engine.
          </p>
        </div>

        <button
          type="button"
          onClick={async () => {
            try {
              setResult(await api.demoSeed());
            } catch (e: any) {
              setError(e.message);
            }
          }}
          className="w-full rounded-xl border border-amber-900/50 bg-amber-950/20 px-4 py-3 text-left"
        >
          <p className="font-medium text-amber-100">Load demo behavior sequence</p>
          <p className="text-xs text-amber-200/60">See tilt without a live broker</p>
        </button>

        <section className="space-y-2">
          <h2 className="text-sm font-semibold text-slate-300">Supported brokers</h2>
          {BROKERS.map((b) => (
            <div
              key={b.id}
              className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium text-white">{b.name}</p>
                <p className="text-xs text-slate-500">{b.method}</p>
              </div>
              <button
                type="button"
                onClick={() => connect(b.id)}
                className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white"
              >
                Connect
              </button>
            </div>
          ))}
        </section>

        {tokenInfo?.api_token && (
          <div className="rounded-xl border border-blue-900/40 bg-blue-950/20 p-4 text-sm text-blue-100">
            <p className="font-medium">API token (copy once)</p>
            <code className="mt-2 block break-all text-xs">{tokenInfo.api_token}</code>
            <p className="mt-2 text-xs text-blue-200/70">
              Header X-API-Key on /api/v1/connectors/&lt;broker&gt;/webhook
            </p>
          </div>
        )}

        {connections.length > 0 && (
          <section className="rounded-xl border border-slate-800 p-4">
            <h2 className="text-sm font-semibold text-slate-300">Active connections</h2>
            <ul className="mt-2 space-y-1 text-sm text-slate-400">
              {connections.map((c) => (
                <li key={c.id}>
                  {c.broker} · {c.status} · {c.account_id || "—"}
                </li>
              ))}
            </ul>
          </section>
        )}

        <section className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          <h2 className="text-sm font-semibold text-white">Upload trades</h2>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setMode("ibkr")}
              className={`rounded-lg px-3 py-1.5 text-xs ${
                mode === "ibkr" ? "bg-blue-600 text-white" : "border border-slate-700 text-slate-400"
              }`}
            >
              IBKR Flex
            </button>
            <button
              type="button"
              onClick={() => setMode("csv")}
              className={`rounded-lg px-3 py-1.5 text-xs ${
                mode === "csv" ? "bg-blue-600 text-white" : "border border-slate-700 text-slate-400"
              }`}
            >
              Generic CSV
            </button>
          </div>
          <input
            value={accountId}
            onChange={(e) => setAccountId(e.target.value)}
            placeholder="Account ID (optional)"
            className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-white"
          />
          <input
            ref={fileRef}
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-slate-400"
          />
          <button
            type="button"
            disabled={!file || loading}
            onClick={upload}
            className="w-full rounded-xl bg-blue-600 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
          >
            {loading ? "Uploading…" : "Upload"}
          </button>
        </section>

        {error && <p className="text-sm text-red-400">{error}</p>}
        {result && (
          <pre className="overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 text-xs text-slate-400">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </main>
    </div>
  );
}
