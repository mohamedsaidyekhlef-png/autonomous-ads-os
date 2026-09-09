import Link from "next/link";

import {
  ArrowUpRight,
  Bot,
  CircleDollarSign,
  Gauge,
  Link2,
  Play,
  Sparkles,
  TrendingUp,
  WalletCards,
} from "lucide-react";

import { SystemStatus } from "@/components/system-status";

const metrics = [
  {
    name: "Revenue",
    value: "$0",
    note: "No connected revenue source",
    icon: CircleDollarSign,
    accent: "text-emerald-600 bg-emerald-50",
  },
  {
    name: "Advertising spend",
    value: "$0",
    note: "No active account data",
    icon: WalletCards,
    accent: "text-blue-600 bg-blue-50",
  },
  {
    name: "Blended ROAS",
    value: "—",
    note: "Awaiting conversion data",
    icon: TrendingUp,
    accent: "text-blue-600 bg-blue-50",
  },
  {
    name: "Tracking confidence",
    value: "—",
    note: "Measurement audit required",
    icon: Gauge,
    accent: "text-amber-600 bg-amber-50",
  },
];

const platforms = [
  {
    name: "Google Ads",
    text: "Search, Shopping and Performance Max",
    mark: "G",
    color: "bg-blue-600",
  },
  {
    name: "Meta Ads",
    text: "Facebook and Instagram",
    mark: "M",
    color: "bg-indigo-600",
  },
  {
    name: "TikTok Ads",
    text: "Creative-first acquisition",
    mark: "T",
    color: "bg-slate-950",
  },
];

export default function OverviewPage() {
  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <section className="relative overflow-hidden rounded-[2rem] bg-[#090d1a] p-7 text-white shadow-2xl shadow-slate-300/60 sm:p-9">
        <div className="absolute -right-24 -top-32 h-80 w-80 rounded-full bg-blue-600/30 blur-3xl" />
        <div className="absolute bottom-[-8rem] left-[30%] h-64 w-64 rounded-full bg-blue-500/20 blur-3xl" />

        <div className="relative grid gap-8 xl:grid-cols-[1fr_auto] xl:items-center">
          <div>
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-blue-400/20 bg-blue-400/10 px-3 py-1.5 text-xs font-semibold text-blue-200">
              <Sparkles size={14} />
              Autonomous media intelligence
            </div>

            <h1 className="max-w-3xl text-3xl font-black tracking-tight sm:text-4xl">
              Build, operate and optimize your advertising from one command
              center.
            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-400">
              Connect Google, Meta and TikTok. Your specialist agents will
              audit measurement, diagnose performance and coordinate execution
              around profitability.
            </p>
          </div>

          <button className="flex items-center justify-center gap-2 rounded-2xl bg-[#FF6500] px-6 py-4 font-bold text-white shadow-xl shadow-orange-950/30 transition hover:-translate-y-0.5 hover:bg-[#E85B00]">
            <Play size={18} fill="currentColor" />
            Start AI Ads Team
          </button>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map(({ name, value, note, icon: Icon, accent }) => (
          <article
            key={name}
            className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
          >
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-slate-500">{name}</p>
              <div className={`rounded-xl p-2.5 ${accent}`}>
                <Icon size={18} />
              </div>
            </div>

            <p className="mt-6 text-3xl font-black tracking-tight">{value}</p>
            <p className="mt-2 text-xs text-slate-500">{note}</p>
          </article>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.5fr_0.75fr]">
        <article className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="font-bold">Advertising network</h2>
              <p className="mt-1 text-sm text-slate-500">
                Authorize platforms through secure OAuth.
              </p>
            </div>
            <Link2 className="text-blue-600" size={21} />
          </div>

          <div className="mt-6 grid gap-3 lg:grid-cols-3">
            {platforms.map((platform) => (
              <Link
                key={platform.name}
                href="/connections"
                className="group rounded-2xl border border-slate-200 p-4 transition hover:border-blue-300 hover:bg-blue-50/40"
              >
                <div className="flex items-center justify-between">
                  <div
                    className={`flex h-11 w-11 items-center justify-center rounded-xl text-sm font-black text-white ${platform.color}`}
                  >
                    {platform.mark}
                  </div>
                  <ArrowUpRight
                    size={17}
                    className="text-slate-400 transition group-hover:text-blue-600"
                  />
                </div>

                <p className="mt-5 font-bold">{platform.name}</p>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  {platform.text}
                </p>

                <div className="mt-4 text-xs font-bold text-blue-600">
                  Connect account
                </div>
              </Link>
            ))}
          </div>
        </article>

        <SystemStatus />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.5fr_0.75fr]">
        <article className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-bold">Intelligence stream</h2>
              <p className="mt-1 text-sm text-slate-500">
                Agent diagnoses, decisions and execution results
              </p>
            </div>
            <Bot size={21} className="text-blue-600" />
          </div>

          <div className="mt-6 flex min-h-56 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50/70 text-center">
            <Bot size={35} className="text-slate-300" />
            <p className="mt-4 font-bold">Agents are waiting for data</p>
            <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
              Connect at least one advertising account before starting the
              measurement and strategy workflows.
            </p>
          </div>
        </article>

        <article className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-bold">Activation requirements</h2>
          <p className="mt-1 text-sm text-slate-500">
            Required before autonomous execution
          </p>

          <div className="mt-6 space-y-3">
            {[
              "Active Whop subscription",
              "Advertising account connected",
              "Conversion tracking verified",
              "Spending limits configured",
              "Initial account audit complete",
            ].map((item, index) => (
              <div
                key={item}
                className="flex items-center gap-3 rounded-xl bg-slate-50 p-3"
              >
                <div className="flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 bg-white text-xs font-black text-slate-400">
                  {index + 1}
                </div>
                <span className="text-sm font-medium text-slate-600">
                  {item}
                </span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
