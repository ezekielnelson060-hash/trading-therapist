"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

const MOTIVES = [
  { id: "planned_setup", label: "Planned setup" },
  { id: "fomo", label: "FOMO" },
  { id: "revenge", label: "Revenge" },
  { id: "fear_of_missing", label: "Fear of missing out" },
  { id: "saw_something", label: "Saw something on the chart" },
  { id: "boredom", label: "Boredom" },
  { id: "other", label: "Other" },
];

export default function CheckInPage() {
  const router = useRouter();
  const [motive, setMotive] = useState("planned_setup");
  const [confidence, setConfidence] = useState(6);
  const [state, setState] = useState(3);
  const [note, setNote] = useState("");
  const [stats, setStats] = useState<any>(null);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        await api.me();
        const s = await api.motiveStats().catch(() => null);
        setStats(s);
      } catch {
        router.push("/login");
      }
    })();
  }, [router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMsg("");
    try {
      await api.createCheckIn({
        motive,
        confidence,
        emotional_state: state,
        note: note || undefined,
      });
      setMsg("Logged. Over time we correlate motives with real outcomes.");
      const s = await api.motiveStats().catch(() => null);
      setStats(s);
    } catch (err: any) {
      setMsg(err.message || "Failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-lg space-y-6 px-4 py-8">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-500">Post-trade check-in</p>
          <h1 className="text-2xl font-bold text-white">Why did you enter?</h1>
          <p className="mt-1 text-sm text-slate-400">
            Optional — turns subjective psychology into measurable behavioral data.
          </p>
        </div>
        <form onSubmit={submit} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <div className="flex flex-wrap gap-2">
            {MOTIVES.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setMotive(m.id)}
                className={`rounded-full px-3 py-1.5 text-xs ${
                  motive === m.id ? "bg-blue-600 text-white" : "border border-slate-700 text-slate-300"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
          <label className="block text-sm text-slate-400">
            Confidence 1–10: {confidence}
            <input type="range" min={1} max={10} value={confidence} onChange={(e) => setConfidence(+e.target.value)} className="mt-1 w-full" />
          </label>
          <label className="block text-sm text-slate-400">
            Emotional state (calm → tilted): {state}
            <input type="range" min={1} max={10} value={state} onChange={(e) => setState(+e.target.value)} className="mt-1 w-full" />
          </label>
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Optional note"
            className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white"
          />
          {msg && <p className="text-sm text-slate-300">{msg}</p>}
          <button type="submit" disabled={loading} className="w-full rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white disabled:opacity-40">
            {loading ? "Saving…" : "Save check-in"}
          </button>
        </form>
        {stats?.motives?.length > 0 && (
          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
            <h2 className="text-sm font-semibold text-slate-300">What your data says</h2>
            <ul className="mt-3 space-y-2">
              {stats.motives.map((m: any) => (
                <li key={m.motive} className="text-sm text-slate-400">
                  <span className="text-amber-400">{m.motive}</span> — {m.insight}
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>
    </div>
  );
}
