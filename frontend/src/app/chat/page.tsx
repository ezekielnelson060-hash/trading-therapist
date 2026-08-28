"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Nav from "@/components/Nav";
import { api } from "@/lib/api";

type Msg = { role: "user" | "assistant"; content: string };

const SUGGESTIONS = [
  "Am I outside my baseline right now?",
  "What is driving my tilt score?",
  "I want to recover losses — talk me out of it",
  "Give me one rule for the rest of the session",
];

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [seeded, setSeeded] = useState(false);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [tilt, setTilt] = useState<any>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    (async () => {
      try {
        await api.me();
        const s = await api.tilt().catch(() => null);
        const tiltData = s?.tilt || null;
        setTilt(tiltData);
        if (!seeded) {
          const score = tiltData?.tilt_score;
          const label = tiltData?.state_label || "unknown";
          const red = tiltData?.signals
            ? Object.values(tiltData.signals).find((x: any) => x.status === "red" || x.status === "amber")
            : null;
          let opener =
            "I reviewed your recent trades and tilt signals. I only use your real data — not motivation slogans.";
          if (score != null) {
            opener = `I reviewed your recent activity. Tilt is ${score}/100 (${label}).`;
            if (red) {
              opener += ` One pattern worth addressing: ${(red as any).label} — ${(red as any).detail}`;
            }
            opener += " Want the cost of this behavior, or one rule for the rest of the session?";
          }
          setMessages([{ role: "assistant", content: opener }]);
          setSeeded(true);
        }
      } catch {
        router.push("/login");
      }
    })();
  }, [router, seeded]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: msg }]);
    setLoading(true);
    try {
      const res = await api.chat(msg, sessionId);
      setSessionId(res.session_id);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
      if (res.tilt_score != null && tilt) {
        setTilt({ ...tilt, tilt_score: res.tilt_score });
      }
    } catch (e: any) {
      setMessages((m) => [...m, { role: "assistant", content: e.message || "Something went wrong." }]);
    } finally {
      setLoading(false);
    }
  }

  const banner =
    tilt?.color === "red"
      ? "border-red-800 bg-red-950/50 text-red-100"
      : tilt?.color === "amber"
        ? "border-amber-800 bg-amber-950/40 text-amber-100"
        : "border-slate-800 bg-slate-900/60 text-slate-300";

  return (
    <div className="flex min-h-screen flex-col bg-[#0b0f14]">
      <Nav />
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-4">
        {tilt && (
          <div className={`mb-3 rounded-xl border px-3 py-2 text-sm ${banner}`}>
            Tilt {tilt.tilt_score}/100 · {tilt.state_label}
            {tilt.do_not_trade ? " · PAUSE recommended" : ""}
          </div>
        )}
        <div className="flex flex-1 flex-col gap-3 overflow-y-auto pb-4">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                m.role === "user"
                  ? "ml-auto bg-blue-600 text-white"
                  : "bg-slate-900 text-slate-200 border border-slate-800"
              }`}
            >
              {m.content}
            </div>
          ))}
          {loading && <p className="text-sm text-slate-500">Reviewing your data…</p>}
          <div ref={bottomRef} />
        </div>
        <div className="flex flex-wrap gap-2 pb-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => send(s)}
              className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400 hover:border-slate-500 hover:text-white"
            >
              {s}
            </button>
          ))}
        </div>
        <form
          className="flex gap-2 border-t border-slate-800 pt-3"
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about tilt, revenge, or plan adherence…"
            className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-white"
          />
          <button type="submit" disabled={loading} className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white">
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
