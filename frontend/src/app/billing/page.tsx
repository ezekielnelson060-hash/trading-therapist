"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

export default function BillingPage() {
  const router = useRouter();
  const [plans, setPlans] = useState<any>(null);
  const [me, setMe] = useState<any>(null);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    (async () => {
      try {
        await api.me();
        const [p, m] = await Promise.all([api.billingPlans(), api.billingMe()]);
        setPlans(p.plans);
        setMe(m);
      } catch {
        router.push("/login");
      }
    })();
  }, [router]);

  async function upgrade(plan: string) {
    setMsg("");
    try {
      const r = await api.checkout(plan);
      if (r.checkout_url) {
        window.location.href = r.checkout_url;
        return;
      }
      setMsg(r.message || `Plan: ${r.plan}`);
      setMe(await api.billingMe());
    } catch (e: any) {
      setMsg(e.message);
    }
  }

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-500">Billing</p>
          <h1 className="text-2xl font-bold text-white">Plans built around risk control</h1>
          <p className="mt-1 text-sm text-slate-400">
            Current: <span className="text-blue-400">{me?.plan || "free"}</span>
          </p>
        </div>
        {msg && <p className="text-sm text-slate-300">{msg}</p>}
        <div className="grid gap-4 sm:grid-cols-2">
          {plans &&
            Object.entries(plans).map(([key, p]: any) => (
              <div key={key} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <h2 className="text-lg font-semibold text-white">{p.name}</h2>
                <p className="mt-1 text-2xl font-bold text-white">
                  ${p.price_usd}
                  <span className="text-sm font-normal text-slate-500">/mo</span>
                </p>
                <ul className="mt-3 space-y-1 text-sm text-slate-400">
                  {(p.features || []).map((f: string) => (
                    <li key={f}>· {f}</li>
                  ))}
                </ul>
                {key !== "free" && (
                  <button
                    type="button"
                    onClick={() => upgrade(key)}
                    className="mt-4 w-full rounded-xl bg-blue-600 py-2.5 text-sm font-semibold text-white"
                  >
                    {me?.plan === key ? "Current" : "Upgrade"}
                  </button>
                )}
              </div>
            ))}
        </div>
        <p className="text-xs text-slate-600">
          Without Stripe keys, upgrade is a demo plan switch. Add STRIPE_SECRET_KEY on Railway for live Checkout.
        </p>
      </main>
    </div>
  );
}
