"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

export default function AlertsPage() {
  const router = useRouter();
  const [alerts, setAlerts] = useState<any[]>([]);
  const [msg, setMsg] = useState("");

  async function load() {
    setAlerts(await api.alerts());
  }

  useEffect(() => {
    (async () => {
      try {
        await api.me();
        await load();
      } catch {
        router.push("/login");
      }
    })();
  }, [router]);

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-lg space-y-6 px-4 py-8">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-500">Alerts</p>
          <h1 className="text-2xl font-bold text-white">Tilt spikes</h1>
          <p className="mt-1 text-sm text-slate-400">In-app always. Email when RESEND_API_KEY is set on Railway.</p>
        </div>
        <button
          type="button"
          className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
          onClick={async () => {
            const r = await api.evaluateAlerts();
            setMsg(
              r.alert_created
                ? `Alert created (email_sent=${r.alert?.email_sent})`
                : `No alert (tilt ${r.tilt_score})`
            );
            await load();
          }}
        >
          Evaluate tilt now
        </button>
        {msg && <p className="text-sm text-slate-400">{msg}</p>}
        <ul className="space-y-2">
          {alerts.map((a) => (
            <li key={a.id} className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm">
              <p className="font-medium text-white">{a.title}</p>
              <p className="mt-1 text-slate-400">{a.body}</p>
              <p className="mt-1 text-xs text-slate-600">
                {a.severity} · {a.email_sent ? "email sent" : "in-app only"}
              </p>
            </li>
          ))}
          {alerts.length === 0 && <p className="text-sm text-slate-500">No alerts yet.</p>}
        </ul>
      </main>
    </div>
  );
}
