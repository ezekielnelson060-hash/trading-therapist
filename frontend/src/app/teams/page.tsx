"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

export default function TeamsPage() {
  const router = useRouter();
  const [teams, setTeams] = useState<any[]>([]);
  const [name, setName] = useState("My desk");
  const [risk, setRisk] = useState<any>(null);
  const [invite, setInvite] = useState("");
  const [msg, setMsg] = useState("");

  async function refresh() {
    const t = await api.teams();
    setTeams(t);
    if (t[0]) setRisk(await api.teamRisk(t[0].id));
  }

  useEffect(() => {
    (async () => {
      try {
        await api.me();
        await refresh();
      } catch {
        router.push("/login");
      }
    })();
  }, [router]);

  return (
    <div className="min-h-screen bg-[#0b0f14]">
      <Nav />
      <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-500">Teams / Prop</p>
          <h1 className="text-2xl font-bold text-white">Desk behavioral risk</h1>
          <p className="mt-1 text-sm text-slate-400">Aggregated tilt — not a P&amp;L leaderboard.</p>
        </div>
        <form
          className="flex gap-2"
          onSubmit={async (e) => {
            e.preventDefault();
            await api.createTeam(name);
            setMsg("Team created");
            await refresh();
          }}
        >
          <input value={name} onChange={(e) => setName(e.target.value)} className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-white" />
          <button type="submit" className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white">Create team</button>
        </form>
        {teams[0] && (
          <form
            className="flex gap-2"
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                await api.inviteTeam(teams[0].id, invite);
                setMsg("Invite ok");
                setInvite("");
                await refresh();
              } catch (err: any) {
                setMsg(err.message);
              }
            }}
          >
            <input value={invite} onChange={(e) => setInvite(e.target.value)} placeholder="Trader email" className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-white" />
            <button type="submit" className="rounded-xl border border-slate-600 px-4 py-2 text-sm text-slate-200">Invite</button>
          </form>
        )}
        {msg && <p className="text-sm text-slate-400">{msg}</p>}
        {risk && (
          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <p className="text-sm text-slate-300">{risk.message}</p>
            <p className="mt-2 text-sm text-amber-400">High risk: {risk.high_risk_count}</p>
            <ul className="mt-4 space-y-2">
              {(risk.traders || []).map((t: any) => (
                <li key={t.user_id} className="flex justify-between rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2 text-sm">
                  <span className="text-slate-300">{t.name || t.email}</span>
                  <span className={t.tilt_score >= 70 ? "text-red-400" : "text-green-400"}>
                    {t.tilt_score}/100 {t.do_not_trade ? "· PAUSE" : ""}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>
    </div>
  );
}
