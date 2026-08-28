"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

function bandColor(band: string) {
  if (band === "high") return "bg-red-950/50 border-red-800 text-red-200";
  if (band === "elevated") return "bg-amber-950/40 border-amber-800 text-amber-100";
  return "bg-green-950/30 border-green-900 text-green-100";
}

export default function TeamsPage() {
  const router = useRouter();
  const [teams, setTeams] = useState<any[]>([]);
  const [name, setName] = useState("Prop desk");
  const [heat, setHeat] = useState<any>(null);
  const [high, setHigh] = useState<any>(null);
  const [invite, setInvite] = useState("");
  const [role, setRole] = useState("trader");
  const [msg, setMsg] = useState("");

  async function refresh() {
    const t = await api.teams();
    setTeams(t);
    if (t[0]) {
      const [h, hr] = await Promise.all([api.teamHeatmap(t[0].id), api.teamHighRisk(t[0].id)]);
      setHeat(h);
      setHigh(hr);
    }
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
          <h1 className="text-2xl font-bold text-white">Behavioral risk infrastructure</h1>
          <p className="mt-1 text-sm text-slate-400">
            Which traders are showing dangerous behavioral deterioration right now?
          </p>
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
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-white"
          />
          <button type="submit" className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white">
            Create desk
          </button>
        </form>

        {teams[0] && (
          <form
            className="flex flex-wrap gap-2"
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                await api.inviteTeam(teams[0].id, invite, role);
                setMsg("Invite ok");
                setInvite("");
                await refresh();
              } catch (err: any) {
                setMsg(err.message);
              }
            }}
          >
            <input
              value={invite}
              onChange={(e) => setInvite(e.target.value)}
              placeholder="Trader email (must have account)"
              className="min-w-[12rem] flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-white"
            />
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            >
              <option value="trader">Trader</option>
              <option value="coach">Coach</option>
              <option value="risk_manager">Risk manager</option>
            </select>
            <button type="submit" className="rounded-xl border border-slate-600 px-4 py-2 text-sm text-slate-200">
              Invite
            </button>
          </form>
        )}

        {msg && <p className="text-sm text-slate-400">{msg}</p>}

        {heat && (
          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <p className="text-sm font-medium text-white">{heat.headline}</p>
            <div className="mt-4 grid grid-cols-3 gap-2 text-center text-sm">
              <div className="rounded-xl border border-green-900/40 bg-green-950/20 py-3">
                <p className="text-xs text-green-400">Controlled</p>
                <p className="text-2xl font-bold text-green-200">{heat.summary?.controlled ?? 0}</p>
              </div>
              <div className="rounded-xl border border-amber-900/40 bg-amber-950/20 py-3">
                <p className="text-xs text-amber-400">Elevated</p>
                <p className="text-2xl font-bold text-amber-200">{heat.summary?.elevated ?? 0}</p>
              </div>
              <div className="rounded-xl border border-red-900/40 bg-red-950/20 py-3">
                <p className="text-xs text-red-400">High risk</p>
                <p className="text-2xl font-bold text-red-200">{heat.summary?.high ?? 0}</p>
              </div>
            </div>
            <div className="mt-4 grid gap-2 sm:grid-cols-2">
              {(heat.cells || []).map((c: any) => (
                <div key={c.user_id} className={`rounded-xl border px-3 py-3 text-sm ${bandColor(c.band)}`}>
                  <div className="flex justify-between gap-2">
                    <span className="truncate font-medium">{c.label}</span>
                    <span className="font-bold tabular-nums">{c.tilt_score}</span>
                  </div>
                  {c.top_signal && <p className="mt-1 line-clamp-2 text-xs opacity-80">{c.top_signal}</p>}
                  {c.do_not_trade && <p className="mt-1 text-xs font-semibold">PAUSE</p>}
                </div>
              ))}
            </div>
          </section>
        )}

        {high && high.count > 0 && (
          <section className="rounded-2xl border border-red-900/50 bg-red-950/20 p-5">
            <h2 className="text-sm font-semibold text-red-300">High risk now ({high.count})</h2>
            <p className="mt-1 text-xs text-red-200/70">{high.message}</p>
            <ul className="mt-3 space-y-2">
              {(high.traders || []).map((t: any) => (
                <li key={t.user_id} className="flex justify-between text-sm text-red-100">
                  <span>{t.name || t.email}</span>
                  <span>
                    {t.tilt_score}/100 · {t.top_signal || t.state_label}
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
