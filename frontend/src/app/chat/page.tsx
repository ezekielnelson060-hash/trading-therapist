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
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      content:
        "I'm your behavioral risk coach. I only use your real trades and tilt signals — not motivation slogans. What's going on?",
    },
  ]);
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
        setTilt(s?.tilt || null);
      } catch {
        router.push("/login");
      }
    })();
  }, [router]);

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
          <div className={`mb-4 rounded-xl border px-4 py-3 text-sm ${banner}`}>
            <span className="font-semibold">Tilt {tilt.tilt_score}/100</span>
            <span className="opacity-80"> · {tilt.state_label}</span>
            {tilt.do_not_trade && <span className="ml-2 font-medium"> — pause recommended</span>}
            <p className="mt-1 text-xs opacity-90">{tilt.recommendation}</p>
          </div>
        )}

        <div className="flex-1 space-y-3 overflow-y-auto pb-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  m.role === "user"
                    ? "bg-blue-600 text-white"
                    : "border border-slate-700/80 bg-slate-900 text-slate-200"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-slate-700/80 bg-slate-900 px-4 py-3 text-sm text-slate-400">
                Checking your data…
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {messages.length <= 2 && !loading && (
          <div className="mb-3 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => send(s)}
                className="rounded-full border border-slate-700 bg-slate-900/80 px-3 py-1.5 text-xs text-slate-300 hover:border-slate-500"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="flex gap-2 border-t border-slate-800 pt-4"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about tilt, revenge, plan adherence…"
            className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white disabled:opacity-40"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
