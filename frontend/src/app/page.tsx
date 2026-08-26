"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("tt_token") : null;
    router.replace(token ? "/dashboard" : "/login");
  }, [router]);
  return <div className="flex min-h-screen items-center justify-center text-slate-400">Loading…</div>;
}
