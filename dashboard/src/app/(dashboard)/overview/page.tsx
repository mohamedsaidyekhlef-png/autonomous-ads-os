"use client";

import Link from "next/link";
import { useState } from "react";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  CircleDollarSign,
  Gauge,
  LoaderCircle,
  Play,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  TriangleAlert,
} from "lucide-react";
import { SiGoogleads, SiMeta, SiTiktok } from "react-icons/si";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";

type StartResult = {
  status?: string;
  message?: string;
  reason?: string;
  next_step?: string;
  run_id?: string;
  mode?: string;
  connected_accounts?: number;
};

const platforms = [
  {
    name: "Google Ads",
    description: "Search, Shopping and Performance Max",
    icon: SiGoogleads,
    iconColor: "#4285F4",
  },
  {
    name: "Meta Ads",
    description: "Facebook and Instagram advertising",
    icon: SiMeta,
    iconColor: "#0866FF",
  },
  {
    name: "TikTok Ads",
    description: "Creative-first customer acquisition",
    icon: SiTiktok,
    iconColor: "#000000",
  },
];

const metrics = [
  {
    label: "Revenue",
    value: "$0",
    note: "No connected revenue source",
    icon: CircleDollarSign,
  },
  {
    label: "Advertising spend",
    value: "$0",
    note: "No active advertising data",
    icon: Activity,
  },
  {
    label: "Blended ROAS",
    value: "—",
    note: "Awaiting conversion data",
    icon: TrendingUp,
  },
  {
    label: "Tracking confidence",
    value: "—",
    note: "Measurement audit required",
    icon: Gauge,
  },
];

export default function OverviewPage() {
  const [starting, setStarting] = useState(false);
  const [result, setResult] = useState<StartResult | null>(null);
  const [requestFailed, setRequestFailed] = useState(false);

  async function startAdsTeam() {
    setStarting(true);
    setRequestFailed(false);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/v1/automation/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mode: "shadow" }),
      });

      const data = (await response.json()) as StartResult;
      setResult(data);

      if (!response.ok && data.status !== "setup_required") {
        setRequestFailed(true);
      }
    } catch {
      setRequestFailed(true);
      setResult({
        status: "failed",
        message:
          "The backend could not be reached. Confirm FastAPI is running on port 8080.",
      });
    } finally {
      setStarting(false);
    }
  }

  const requiresConnection =
    result?.status === "setup_required" ||
    result?.reason === "no_connected_ad_accounts";

  return (
    <main className="space-y-5">
      <section className="relative overflow-hidden rounded-[30px] bg-[#1468F3] px-6 py-8 text-white shadow-[0_20px_60px_rgba(20,104,243,0.22)] md:px-10 md:py-10">
        <div className="absolute -right-20 -top-24 h-64 w-64 rounded-full bg-white/12" />
        <div className="absolute -bottom-28 right-32 h-64 w-64 rounded-full bg-[#FF6500]/30" />

        <div className="relative z-10 flex flex-col gap-7 xl:flex-row xl:items-center xl:justify-between">
          <div className="max-w-3xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/25 bg-white/12 px-4 py-2 text-xs font-bold uppercase tracking-[0.16em]">
              <Sparkles className="h-4 w-4" />
              Autonomous advertising intelligence
            </div>

            <h1 className="max-w-3xl text-3xl font-black leading-tight tracking-[-0.04em] md:text-5xl">
              Build, operate and optimize advertising from one command center.
            </h1>

            <p className="mt-5 max-w-2xl text-sm leading-7 text-white/85 md:text-base">
              Connect your platforms, validate measurement and launch the
              specialist AI team in protected shadow mode.
            </p>
          </div>

          <button
            type="button"
            onClick={startAdsTeam}
            disabled={starting}
            className="inline-flex min-h-14 shrink-0 items-center justify-center gap-3 rounded-2xl bg-[#FF6500] px-7 py-4 text-sm font-black text-white shadow-[0_14px_35px_rgba(255,101,0,0.35)] transition hover:-translate-y-0.5 hover:bg-[#E85B00] disabled:cursor-not-allowed disabled:opacity-70"
          >
            {starting ? (
              <LoaderCircle className="h-5 w-5 animate-spin" />
            ) : (
              <Play className="h-5 w-5 fill-current" />
            )}
            {starting ? "Checking readiness…" : "Start AI Ads Team"}
          </button>
        </div>
      </section>

      {result && (
        <section
          className={`rounded-2xl border p-5 ${
            requiresConnection
              ? "border-[#FF6500]/30 bg-[#FF6500]/8"
              : requestFailed
                ? "border-red-200 bg-red-50"
                : "border-[#1468F3]/25 bg-[#1468F3]/5"
          }`}
        >
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex items-start gap-3">
              {requiresConnection ? (
                <TriangleAlert className="mt-0.5 h-5 w-5 shrink-0 text-[#FF6500]" />
              ) : requestFailed ? (
                <TriangleAlert className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
              ) : (
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-[#1468F3]" />
              )}

              <div>
                <p className="font-bold text-neutral-950">
                  {requiresConnection
                    ? "Platform connection required"
                    : requestFailed
                      ? "Readiness check failed"
                      : "Readiness check completed"}
                </p>
                <p className="mt-1 text-sm leading-6 text-neutral-600">
                  {result.message}
                </p>

                {result.run_id && (
                  <p className="mt-2 font-mono text-xs text-neutral-500">
                    Run ID: {result.run_id}
                  </p>
                )}
              </div>
            </div>

            {requiresConnection && (
              <Link
                href="/connections"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#FF6500] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#E85B00]"
              >
                Connect accounts
                <ArrowRight className="h-4 w-4" />
              </Link>
            )}

            {requestFailed && (
              <button
                type="button"
                onClick={startAdsTeam}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#1468F3] px-5 py-3 text-sm font-bold text-white"
              >
                <RefreshCw className="h-4 w-4" />
                Retry
              </button>
            )}
          </div>
        </section>
      )}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;

          return (
            <article
              key={metric.label}
              className="rounded-3xl border border-neutral-200 bg-white p-6 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-neutral-600">
                  {metric.label}
                </p>

                <span className="grid h-10 w-10 place-items-center rounded-xl bg-[#1468F3]/10 text-[#1468F3]">
                  <Icon className="h-5 w-5" />
                </span>
              </div>

              <p className="mt-7 text-3xl font-black tracking-tight text-neutral-950">
                {metric.value}
              </p>

              <p className="mt-2 text-xs leading-5 text-neutral-500">
                {metric.note}
              </p>
            </article>
          );
        })}
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.5fr_0.8fr]">
        <article className="rounded-3xl border border-neutral-200 bg-white p-6 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-black text-neutral-950">
                Advertising networks
              </h2>
              <p className="mt-1 text-sm text-neutral-500">
                Authorize platforms using secure OAuth.
              </p>
            </div>

            <Link
              href="/connections"
              className="text-sm font-bold text-[#1468F3]"
            >
              View all
            </Link>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {platforms.map((platform) => {
              const Logo = platform.icon;

              return (
                <Link
                  key={platform.name}
                  href="/connections"
                  className="group rounded-2xl border border-neutral-200 bg-white p-5 transition hover:-translate-y-1 hover:border-[#1468F3]/40 hover:shadow-lg"
                >
                  <div className="flex items-center justify-between">
                    <span className="grid h-14 w-14 place-items-center rounded-2xl bg-neutral-50">
                      <Logo
                        className="h-8 w-8"
                        style={{ color: platform.iconColor }}
                        aria-label={`${platform.name} logo`}
                      />
                    </span>

                    <ArrowRight className="h-4 w-4 text-neutral-400 transition group-hover:translate-x-1 group-hover:text-[#1468F3]" />
                  </div>

                  <h3 className="mt-6 text-lg font-black text-neutral-950">
                    {platform.name}
                  </h3>

                  <p className="mt-1 min-h-10 text-sm leading-5 text-neutral-500">
                    {platform.description}
                  </p>

                  <span className="mt-5 inline-flex text-sm font-bold text-[#1468F3]">
                    Connect account
                  </span>
                </Link>
              );
            })}
          </div>
        </article>

        <article className="rounded-3xl border border-neutral-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-black text-neutral-950">
            Capital protection
          </h2>

          <p className="mt-1 text-sm text-neutral-500">
            Live spending remains protected until validation passes.
          </p>

          <div className="mt-6 rounded-2xl bg-[#1468F3]/7 p-5">
            <ShieldCheck className="h-9 w-9 text-[#1468F3]" />

            <h3 className="mt-4 font-black text-neutral-950">
              Shadow mode active
            </h3>

            <p className="mt-2 text-sm leading-6 text-neutral-600">
              The system can inspect readiness without changing advertising
              campaigns or spending money.
            </p>
          </div>

          <Link
            href="/connections"
            className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#FF6500] px-5 py-3.5 text-sm font-black text-white transition hover:bg-[#E85B00]"
          >
            Complete setup
            <ArrowRight className="h-4 w-4" />
          </Link>
        </article>
      </section>
    </main>
  );
}
