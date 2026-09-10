"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Bot, CheckCircle2, Clock3, LoaderCircle, Send, Sparkles } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";

type Recommendation = { title: string; rationale: string; expected_impact: string; risk: string; confidence: number; measurement: string };
type Run = { run_id: string; status: "queued" | "running" | "completed" | "failed"; mode: string; elapsed_seconds?: number; error_message?: string | null; result?: { executive_summary: string; diagnosis: string[]; recommendations: Recommendation[] } | null };

function duration(seconds = 0) { return seconds < 60 ? `${seconds}s` : `${Math.floor(seconds / 60)}m ${seconds % 60}s`; }

export function AgentCommandCenter() {
  const [command, setCommand] = useState("");
  const [run, setRun] = useState<Run | null>(() => {
    if (typeof window === "undefined") return null;
    try {
      const saved = window.localStorage.getItem("ads-os:last-run");
      return saved ? (JSON.parse(saved) as Run) : null;
    } catch {
      window.localStorage.removeItem("ads-os:last-run");
      return null;
    }
  });
  const [error, setError] = useState("");
  const active = run?.status === "queued" || run?.status === "running";

  useEffect(() => {
    if (!run || !active) return;
    const timer = window.setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/v1/command/runs/${run.run_id}`);
        if (response.ok) setRun((await response.json()) as Run);
      } catch { /* keep the saved run visible and retry */ }
    }, 1500);
    return () => window.clearInterval(timer);
  }, [active, run]);

  useEffect(() => { if (run) window.localStorage.setItem("ads-os:last-run", JSON.stringify(run)); }, [run]);

  async function submitCommand() {
    if (command.trim().length < 5) { setError("Describe what you want the AI Ads Team to accomplish."); return; }
    setError(""); setRun(null);
    try {
      const response = await fetch(`${API_URL}/v1/command/runs`, { method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ command: command.trim(), mode: "shadow", create_campaign_draft: true, selected_agents: ["chief_strategy", "measurement_auditor", "budget_controller", "risk_controller"] }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "The command could not be queued.");
      setRun(payload as Run);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "The command could not be queued."); }
  }

  const statusLabel = useMemo(() => run?.status ? `${run.status[0].toUpperCase()}${run.status.slice(1)}` : "", [run]);
  return <section className="overflow-hidden rounded-3xl border border-[#1468F3]/15 bg-white shadow-[0_18px_50px_rgba(20,104,243,0.08)]">
    <div className="border-b border-neutral-200 bg-gradient-to-r from-[#1468F3]/[0.07] to-[#FF6500]/[0.05] p-6">
      <div className="flex items-start gap-4"><span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#1468F3] text-white"><Bot className="h-6 w-6" /></span><div><div className="flex items-center gap-2"><h2 className="text-xl font-black text-neutral-950">Command your AI Ads Team</h2><Sparkles className="h-4 w-4 text-[#FF6500]" /></div><p className="mt-1 text-sm leading-6 text-neutral-600">Durable, protected shadow-mode analysis. No advertising action or spend is performed.</p></div></div>
      <div className="mt-5 rounded-2xl border border-neutral-200 bg-white p-3 shadow-sm"><textarea value={command} onChange={(event) => setCommand(event.target.value)} placeholder="Example: Build a protected Google Search campaign draft for my service." rows={4} disabled={active} className="w-full resize-none border-0 bg-transparent px-2 py-2 text-base leading-7 text-neutral-950 outline-none placeholder:text-neutral-400" /><div className="flex flex-col gap-3 border-t border-neutral-100 pt-3 sm:flex-row sm:items-center sm:justify-between"><div className="flex gap-2 text-xs font-semibold"><span className="rounded-full bg-[#1468F3]/10 px-3 py-1.5 text-[#1468F3]">Shadow mode</span><span className="rounded-full bg-[#FF6500]/10 px-3 py-1.5 text-[#FF6500]">DRY_RUN mandatory</span></div><button type="button" onClick={submitCommand} disabled={active} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-[#FF6500] px-5 py-3 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-60">{active ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}{active ? "Queued for specialists…" : "Run AI Ads Team"}</button></div></div>
    </div>
    {error && <div className="flex gap-3 border-b border-red-200 bg-red-50 p-5 text-sm text-red-700"><AlertTriangle className="h-5 w-5" />{error}</div>}
    {run && <div className="space-y-5 p-6"><div className={`flex items-start gap-3 rounded-2xl p-5 ${run.status === "failed" ? "bg-red-50 text-red-800" : "bg-[#1468F3]/[0.06]"}`}>{run.status === "completed" ? <CheckCircle2 className="h-5 w-5 text-[#1468F3]" /> : run.status === "failed" ? <AlertTriangle className="h-5 w-5" /> : <LoaderCircle className="h-5 w-5 animate-spin text-[#1468F3]" />}<div><p className="font-black text-neutral-950">{statusLabel} shadow run</p><p className="mt-1 flex items-center gap-1 text-sm text-neutral-600"><Clock3 className="h-4 w-4" />Elapsed {duration(run.elapsed_seconds)}</p><p className="mt-2 font-mono text-xs text-neutral-500">Run: {run.run_id}</p>{run.error_message && <p className="mt-3 text-sm text-red-700">{run.error_message}</p>}</div></div>
    {run.result && <><p className="text-sm leading-6 text-neutral-700">{run.result.executive_summary}</p><div><h3 className="text-sm font-black uppercase tracking-[0.12em] text-neutral-500">Diagnosis</h3><ul className="mt-3 space-y-2">{run.result.diagnosis.map((item) => <li key={item} className="rounded-xl border border-neutral-200 p-4 text-sm text-neutral-700">{item}</li>)}</ul></div><div className="grid gap-4 lg:grid-cols-2">{run.result.recommendations.map((item, index) => <article key={`${item.title}-${index}`} className="rounded-2xl border border-neutral-200 p-5"><div className="flex justify-between gap-2"><h4 className="font-black">{item.title}</h4><span className="text-sm font-bold text-[#1468F3]">{Math.round(item.confidence * 100)}%</span></div><p className="mt-3 text-sm text-neutral-600">{item.rationale}</p><p className="mt-4 text-xs text-neutral-500">Expected: {item.expected_impact} · Risk: {item.risk}<br />Measure: {item.measurement}</p></article>)}</div></>}</div>}
  </section>;
}
