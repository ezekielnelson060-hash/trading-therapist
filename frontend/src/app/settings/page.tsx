"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const router = useRouter();
  const [me, setMe] = useState<any>(null);
  const [lock, setLock] = useState<any>(null);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setMe(await api.me());
        setLock(await api.lockStatus().catch(() => null));
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
          <p className="text-xs uppercase tracking-widest text-slate-500">Settings</p>
          <h1 className="text-2xl font-bold text-white">Account</h1>
        </div>
        {me && (
          <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-300">
            <p>{me.email}</p>
            <p className="mt-1 text-slate-500">Plan: {me.plan || "free"}</p>
          </section>
        )}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
          <h2 className="text-sm font-semibold text-slate-300">Soft trading lock</h2>
          <p className="mt-1 text-xs text-slate-500">
            In-app only — cannot force-close broker positions without broker API rights.
          </p>
          <p className="mt-2 text-sm text-white">{lock?.locked ? `Locked until ${lock.until || "—"}` : "Not locked"}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded-lg bg-red-800 px-3 py-1.5 text-xs font-semibold text-white"
              onClick={async () => {
                const r = await api.engageLock(60);
                setMsg(r.message);
                setLock(await api.lockStatus());
              }}
            >
              Lock 60 min
            </button>
            <button
              type="button"
              className="rounded-lg border border-slate-600 px-3 py-1.5 text-xs text-slate-300"
              onClick={async () => {
                const r = await api.autoLock();
                setMsg(r.message);
                setLock(await api.lockStatus());
              }}
            >
              Auto from tilt
            </button>
            <button
              type="button"
              className="rounded-lg border border-slate-600 px-3 py-1.5 text-xs text-slate-300"
              onClick={async () => {
                const r = await api.releaseLock();
                setMsg(r.message);
                setLock(await api.lockStatus());
              }}
            >
              Release
            </button>
          </div>
          {msg && <p className="mt-2 text-xs text-slate-400">{msg}</p>}
        </section>
        <button type="button" onClick={() => router.push("/onboarding")} className="text-sm text-blue-400 hover:underline">
          Replay onboarding →
        </button>
      </main>
    </div>
  );
}
