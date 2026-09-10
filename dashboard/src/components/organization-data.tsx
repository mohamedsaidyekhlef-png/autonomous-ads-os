"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Database, LoaderCircle } from "lucide-react";

const API_URL = process.env.NODE_ENV === "production" ? "/api" : process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";
const titles: Record<string, string> = { campaigns: "Campaign drafts", decisions: "Decision journal", experiments: "Experiment laboratory", creative: "Creative lab", reports: "Executive reports", settings: "Workspace settings" };

export function OrganizationData({ resource }: { resource: keyof typeof titles }) {
  const [items, setItems] = useState<Record<string, unknown>[] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { fetch(`${API_URL}/v1/${resource}`).then(async response => { if (!response.ok) throw new Error("Data is unavailable until an authorized organization is selected."); return response.json(); }).then(setItems).catch(caught => setError(caught instanceof Error ? caught.message : "Unable to load data.")); }, [resource]);
  return <div className="mx-auto max-w-[1600px] space-y-7"><header><p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-600">Organization data</p><h1 className="mt-1 text-3xl font-black tracking-tight">{titles[resource]}</h1><p className="mt-2 text-sm text-slate-500">Persisted, organization-isolated shadow-mode records. Live platform actions are unavailable.</p></header><section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">{error ? <div className="flex gap-3 text-sm text-amber-700"><AlertTriangle />{error}</div> : items === null ? <LoaderCircle className="animate-spin text-[#1468F3]" /> : items.length === 0 ? <div className="flex items-center gap-3 text-sm text-slate-500"><Database />No saved {resource} yet.</div> : <div className="space-y-3">{items.map(item => <article key={String(item.id ?? item.key)} className="rounded-2xl border border-slate-200 p-4"><p className="font-bold text-slate-950">{String(item.name ?? item.key ?? item.objective ?? item.report_type)}</p><p className="mt-1 text-sm text-slate-600">{String(item.status ?? item.rationale ?? "Saved shadow-mode record")}</p></article>)}</div>}</section></div>;
}

