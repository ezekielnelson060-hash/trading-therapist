"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

export default function ImportPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState("");

  useEffect(() => {
    api.me().catch(() => router.push("/login"));
  }, [router]);

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
      <main className="mx-auto max-w-lg space-y-8 px-4 py-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Import real trades</h1>
          <p className="mt-1 text-sm text-slate-400">No manual journaling. Pull from broker data only.</p>
        </div>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="mb-2 font-semibold text-white">MT5 webhook</h2>
          <p className="mb-4 text-sm text-slate-400">Create a connection token for the Expert Advisor.</p>
          <button type="button" onClick={connectMt5} className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white">
            Generate MT5 token
          </button>
          {token && (
            <p className="mt-3 break-all rounded-lg bg-slate-950 p-3 text-xs text-green-400">Token: {token}</p>
          )}
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="mb-2 font-semibold text-white">IBKR Flex Query CSV</h2>
          <form onSubmit={upload} className="space-y-4">
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full text-sm text-slate-300"
            />
            <button type="submit" disabled={!file || loading} className="w-full rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white disabled:opacity-40">
              {loading ? "Uploading…" : "Upload CSV"}
            </button>
          </form>
          {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
          {result && (
            <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-300">{JSON.stringify(result, null, 2)}</pre>
          )}
        </section>
      </main>
    </div>
  );
}
