"use client";

import {
  Activity,
  BarChart3,
  Bell,
  Bot,
  Brain,
  CheckCircle2,
  ChevronRight,
  CircleDollarSign,
  Clock3,
  Cloud,
  Code2,
  CreditCard,
  Database,
  FlaskConical,
  Gauge,
  Image,
  KeyRound,
  Link2,
  LockKeyhole,
  Mail,
  Megaphone,
  MessageCircle,
  Pause,
  Play,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  TriangleAlert,
  WalletCards,
  Zap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

function PageHeader({
  eyebrow,
  title,
  description,
  icon: Icon,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  icon: LucideIcon;
  action?: string;
}) {
  return (
    <header className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
      <div className="flex items-start gap-4">
        <div className="rounded-2xl bg-gradient-to-br from-[#1468F3] to-[#1468F3] p-3 text-white shadow-lg shadow-blue-200">
          <Icon size={25} />
        </div>

        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-600">
            {eyebrow}
          </p>
          <h1 className="mt-1 text-3xl font-black tracking-tight">{title}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            {description}
          </p>
        </div>
      </div>

      {action && (
        <button className="flex items-center justify-center gap-2 rounded-xl bg-[#1468F3] px-5 py-3 text-sm font-bold text-white shadow-lg transition hover:-translate-y-0.5 hover:bg-blue-700">
          <Plus size={17} />
          {action}
        </button>
      )}
    </header>
  );
}

function StatusBadge({
  label,
  color = "slate",
}: {
  label: string;
  color?: "green" | "amber" | "blue" | "violet" | "slate";
}) {
  const colors = {
    green: "border-emerald-200 bg-emerald-50 text-emerald-700",
    amber: "border-amber-200 bg-amber-50 text-amber-700",
    blue: "border-blue-200 bg-blue-50 text-blue-700",
    violet: "border-blue-200 bg-blue-50 text-blue-700",
    slate: "border-slate-200 bg-slate-50 text-slate-600",
  };

  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide ${colors[color]}`}
    >
      {label}
    </span>
  );
}

function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: string;
}) {
  return (
    <div className="flex min-h-56 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 p-8 text-center">
      <div className="rounded-2xl bg-white p-3 text-slate-400 shadow-sm">
        <Icon size={27} />
      </div>
      <p className="mt-4 font-bold">{title}</p>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
        {description}
      </p>
      {action && (
        <button className="mt-5 rounded-xl bg-[#1468F3] px-5 py-2.5 text-sm font-bold text-white">
          {action}
        </button>
      )}
    </div>
  );
}

function ConnectionsPage() {
  const platforms = [
    {
      name: "Google Ads",
      description: "Search, Shopping, YouTube and Performance Max",
      mark: "G",
      color: "bg-blue-600",
      permission: "OAuth + developer token",
    },
    {
      name: "Meta Ads",
      description: "Facebook and Instagram campaign management",
      mark: "M",
      color: "bg-indigo-600",
      permission: "Marketing API OAuth",
    },
    {
      name: "TikTok Ads",
      description: "Campaign, creative and audience management",
      mark: "T",
      color: "bg-[#1468F3]",
      permission: "TikTok Business OAuth",
    },
    {
      name: "Search Console",
      description: "Organic demand and landing-page intelligence",
      mark: "SC",
      color: "bg-emerald-600",
      permission: "Google OAuth",
    },
  ];

  return (
    <div className="mx-auto max-w-[1600px] space-y-7">
      <PageHeader
        eyebrow="Data and execution"
        title="Platform Connections"
        description="Authorize customer-owned accounts through official OAuth. Access tokens will be encrypted and isolated by organization."
        icon={Link2}
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {platforms.map((platform) => (
          <article
            key={platform.name}
            className="group rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:border-blue-300 hover:shadow-lg"
          >
            <div className="flex items-start justify-between">
              <div
                className={`flex h-12 w-12 items-center justify-center rounded-2xl text-sm font-black text-white ${platform.color}`}
              >
                {platform.mark}
              </div>
              <StatusBadge label="Not connected" color="amber" />
            </div>

            <h2 className="mt-6 font-bold">{platform.name}</h2>
            <p className="mt-2 min-h-10 text-xs leading-5 text-slate-500">
              {platform.description}
            </p>

            <div className="mt-5 flex items-center gap-2 text-xs text-slate-500">
              <KeyRound size={14} />
              {platform.permission}
            </div>

            <button className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-[#1468F3] px-4 py-3 text-sm font-bold text-white transition group-hover:bg-blue-700">
              <Link2 size={16} />
              Connect {platform.name}
            </button>
          </article>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
        <article className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-bold">Connected advertising accounts</h2>
              <p className="mt-1 text-sm text-slate-500">
                Accounts authorized for reporting and execution
              </p>
            </div>
            <Search size={20} className="text-slate-400" />
          </div>

          <div className="mt-6">
            <EmptyState
              icon={Cloud}
              title="No advertising accounts connected"
              description="Connect a platform above. After OAuth authorization, the system will discover the advertising accounts available to the customer."
            />
          </div>
        </article>

        <article className="rounded-[1.75rem] bg-[#1468F3] p-6 text-white shadow-xl">
          <LockKeyhole className="text-emerald-400" size={25} />
          <h2 className="mt-5 text-xl font-bold">Credential protection</h2>
          <p className="mt-3 text-sm leading-7 text-slate-400">
            Customer passwords are never collected. OAuth tokens are encrypted
            before storage and are never exposed to language models.
          </p>

          <div className="mt-6 space-y-3">
            {[
              "Encrypted token vault",
              "Organization-level isolation",
              "Scope and expiration tracking",
              "Immediate revocation support",
            ].map((item) => (
              <div key={item} className="flex items-center gap-3 text-sm">
                <CheckCircle2 size={16} className="text-emerald-400" />
                {item}
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}

function CampaignsPage() {
  const stats = [
    ["Active campaigns", "0", Megaphone],
    ["Spend today", "$0", WalletCards],
    ["Revenue today", "$0", CircleDollarSign],
    ["Blended ROAS", "—", TrendingUp],
  ] as const;

  return (
    <div className="mx-auto max-w-[1600px] space-y-7">
      <PageHeader
        eyebrow="Cross-platform operations"
        title="Unified Campaigns"
        description="View Google, Meta and TikTok campaign performance in one normalized operating layer."
        icon={Megaphone}
        action="Create campaign"
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map(([label, value, Icon]) => (
          <article
            key={label}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-slate-500">{label}</p>
              <Icon size={18} className="text-blue-600" />
            </div>
            <p className="mt-5 text-3xl font-black">{value}</p>
          </article>
        ))}
      </section>

      <section className="overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-4 border-b border-slate-200 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-bold">Campaign portfolio</h2>
            <p className="mt-1 text-xs text-slate-500">
              Normalized real-time platform performance
            </p>
          </div>

          <div className="flex gap-2">
            <button className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold">
              All platforms
            </button>
            <button className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold">
              All statuses
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-left">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                {[
                  "Campaign",
                  "Platform",
                  "Status",
                  "Spend",
                  "Revenue",
                  "CPA",
                  "ROAS",
                  "Agent diagnosis",
                ].map((heading) => (
                  <th key={heading} className="px-5 py-4 font-bold">
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
          </table>
        </div>

        <div className="p-6">
          <EmptyState
            icon={Megaphone}
            title="No campaign data"
            description="Campaigns will appear after an advertising account is connected and the first synchronization completes."
            action="Open connections"
          />
        </div>
      </section>
    </div>
  );
}

function AgentsPage() {
  const agents = [
    {
      name: "Chief Strategist",
      role: "Cross-channel objectives and arbitration",
      icon: Brain,
    },
    {
      name: "Measurement Auditor",
      role: "Tracking integrity and data confidence",
      icon: Gauge,
    },
    {
      name: "Google Ads Specialist",
      role: "Search, Shopping and Performance Max",
      icon: Search,
    },
    {
      name: "Meta Ads Specialist",
      role: "Audience, delivery and creative performance",
      icon: Target,
    },
    {
      name: "TikTok Specialist",
      role: "Creative-first acquisition strategy",
      icon: Zap,
    },
    {
      name: "Budget Controller",
      role: "Pacing, marginal returns and capital allocation",
      icon: WalletCards,
    },
    {
      name: "Creative Director",
      role: "Concept portfolio and fatigue management",
      icon: Sparkles,
    },
    {
      name: "Risk Controller",
      role: "Anomalies, account safety and emergency stops",
      icon: ShieldCheck,
    },
  ];

  return (
    <div className="mx-auto max-w-[1600px] space-y-7">
      <PageHeader
        eyebrow="Multi-agent intelligence"
        title="AI Agent Team"
        description="Each specialist has a bounded mandate, typed decisions, dedicated tools and measurable responsibilities."
        icon={Bot}
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {agents.map(({ name, role, icon: Icon }) => (
          <article
            key={name}
            className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-start justify-between">
              <div className="rounded-2xl bg-blue-50 p-3 text-blue-600">
                <Icon size={21} />
              </div>
              <StatusBadge label="Waiting" />
            </div>

            <h2 className="mt-5 font-bold">{name}</h2>
            <p className="mt-2 min-h-10 text-xs leading-5 text-slate-500">
              {role}
            </p>

            <div className="mt-5 border-t border-slate-100 pt-4">
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Confidence</span>
                <span className="font-bold">No data</span>
              </div>
              <div className="mt-2 h-1.5 rounded-full bg-slate-100" />
            </div>
          </article>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
        <article className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-bold">Live intelligence stream</h2>
          <p className="mt-1 text-sm text-slate-500">
            Reasoning tasks, diagnoses and proposed actions
          </p>

          <div className="mt-6">
            <EmptyState
              icon={Brain}
              title="Agent team not activated"
              description="Complete the account connection, measurement audit and policy configuration before starting the agent team."
            />
          </div>
        </article>

        <article className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-bold">Autonomy controller</h2>
          <p className="mt-1 text-sm text-slate-500">
            Current system authority
          </p>

          <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4">
            <div className="flex items-center gap-2 font-bold text-amber-800">
              <Pause size={18} />
              Dry-run mode
            </div>
            <p className="mt-2 text-sm leading-6 text-amber-700">
              Agents may analyze and propose, but no advertising mutation is
              currently authorized.
            </p>
          </div>

          <button className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-[#1468F3] px-5 py-3 text-sm font-bold text-white">
            <Play size={17} />
            Configure activation
          </button>
        </article>
      </section>
    </div>
  );
}

function DecisionsPage() {
  const stages = [
    ["Observe", Database],
    ["Diagnose", Brain],
    ["Policy check", ShieldCheck],
    ["Execute", Zap],
    ["Verify", CheckCircle2],
  ] as const;

  return (
    <div className="mx-auto max-w-[1600px] space-y-7">
      <PageHeader
        eyebrow="Transparent autonomy"
        title="Decision Journal"
        description="Audit every observation, hypothesis, action, policy result, execution and measured outcome."
        icon={Activity}
      />

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-bold">Decision lifecycle</h2>

        <div className="mt-6 grid gap-3 md:grid-cols-5">
          {stages.map(([name, Icon], index) => (
            <div
              key={name}
              className="relative rounded-2xl border border-slate-200 bg-slate-50 p-4"
            >
              <div className="flex items-center justify-between">
                <Icon size={19} className="text-blue-600" />
                <span className="text-xs font-black text-slate-300">
                  0{index + 1}
                </span>
              </div>
              <p className="mt-4 text-sm font-bold">{name}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
        <EmptyState
          icon={Activity}
          title="No decisions recorded"
          description="The journal will contain evidence, alternatives, confidence, risk, policy evaluation, API verification and delayed outcomes."
        />
      </section>
    </div>
  );
}

function ExperimentsPage() {
  return (
    <div className="mx-auto max-w-[1600px] space-y-7">
      <PageHeader
        eyebrow="Controlled learning"
        title="Experiment Laboratory"
        description="Run hypothesis-driven tests without allowing unrelated autonomous changes to corrupt the result."
        icon={FlaskConical}
        action="Design experiment"
      />

      <section className="grid gap-4 md:grid-cols-3">
        {[
          ["Active tests", "0", FlaskConical, "violet"],
          ["Awaiting results", "0", Clock3, "amber"],
          ["Validated learnings", "0", CheckCircle2, "green"],
        ].map(([name, value, RawIcon, color]) => {
          const Icon = RawIcon as LucideIcon;

          return (
            <article
              key={name as string}
              className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm"
            >
              <Icon size={21} className="text-blue-600" />
              <p className="mt-5 text-sm font-semibold text-slate-500">
                {name as string}
              </p>
              <p className="mt-2 text-4xl font-black">{value as string}</p>
              <div className="mt-3">
                <StatusBadge
                  label="No data"
                  color={color as "violet" | "amber" | "green"}
                />
              </div>
            </article>
          );
        })}
      </section>

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
        <EmptyState
          icon={FlaskConical}
          title="No experiments running"
          description="Create a hypothesis with a control, treatment, primary metric, minimum sample and stopping conditions."
          action="Create first experiment"
        />
      </section>
    </div>
  );
}

function CreativePage() {
  const pipeline = [
    ["Research", "0 insights", Search],
    ["Concepts", "0 concepts", Sparkles],
    ["Production", "0 assets", Image],
    ["Testing", "0 active", FlaskConical],
  ] as const;

  return (
    <div className="mx-auto max-w-[1600px] space-y-7">
      <PageHeader
        eyebrow="Creative intelligence"
        title="Creative Lab"
        description="Turn customer language, performance evidence and market research into structured creative experiments."
        icon={Sparkles}
        action="New creative brief"
      />

      <section className="grid gap-4 lg:grid-cols-4">
        {pipeline.map(([name, count, Icon]) => (
          <article
            key={name}
            className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm"
          >
            <Icon size={21} className="text-blue-600" />
            <p className="mt-5 font-bold">{name}</p>
            <p className="mt-1 text-sm text-slate-500">{count}</p>
          </article>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <article className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
          <EmptyState
            icon={Image}
            title="Creative portfolio is empty"
            description="Connect an advertising account to import existing assets and establish creative performance baselines."
          />
        </article>

        <article className="rounded-[1.75rem] bg-gradient-to-br from-[#1468F3] to-[#1468F3] p-6 text-white shadow-xl">
          <Code2 size={24} className="text-blue-200" />
          <h2 className="mt-5 text-xl font-bold">Creative memory</h2>
          <p className="mt-3 text-sm leading-7 text-blue-100/70">
            The system will learn at the level of hooks, problems, promises,
            proof, objections, offers and visual styles—not just filenames.
          </p>
        </article>
      </section>
    </div>
  );
}

function ReportsPage() {
  return (
    <div className="mx-auto max-w-[1600px] space-y-7">
      <PageHeader
        eyebrow="Performance intelligence"
        title="Executive Reports"
        description="Understand channel performance, profitability, agent contribution and business risk."
        icon={BarChart3}
        action="Generate report"
      />

      <section className="grid gap-4 md:grid-cols-3">
        {[
          ["Daily brief", "Yesterday's performance and actions", Clock3],
          ["Weekly strategy", "Trends, tests and budget changes", TrendingUp],
          ["Monthly executive", "Profitability and strategic conclusions", BarChart3],
        ].map(([name, description, RawIcon]) => {
          const Icon = RawIcon as LucideIcon;

          return (
            <article
              key={name as string}
              className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm"
            >
              <Icon size={21} className="text-blue-600" />
              <h2 className="mt-5 font-bold">{name as string}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                {description as string}
              </p>
              <button className="mt-5 flex items-center gap-2 text-sm font-bold text-blue-600">
                Configure
                <ChevronRight size={16} />
              </button>
            </article>
          );
        })}
      </section>

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
        <EmptyState
          icon={BarChart3}
          title="Reporting begins after synchronization"
          description="The system needs advertising and conversion data before generating useful executive reports."
        />
      </section>
    </div>
  );
}

function NotificationsPage() {
  const channels = [
    ["Email", "Daily and weekly reports", Mail, "Available"],
    ["Slack", "Workspace alerts and summaries", MessageCircle, "Connect"],
    ["Telegram", "Instant bot notifications", MessageCircle, "Connect"],
    ["WhatsApp", "Approved business messages", MessageCircle, "Connect"],
  ] as const;

  return (
    <div className="mx-auto max-w-[1600px] space-y-7">
      <PageHeader
        eyebrow="Stay informed"
        title="Notification Center"
        description="Receive daily summaries, performance warnings and critical account alerts."
        icon={Bell}
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {channels.map(([name, description, Icon, status]) => (
          <article
            key={name}
            className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-start justify-between">
              <div className="rounded-xl bg-blue-50 p-2.5 text-blue-600">
                <Icon size={20} />
              </div>
              <StatusBadge
                label={status}
                color={status === "Available" ? "green" : "slate"}
              />
            </div>

            <h2 className="mt-5 font-bold">{name}</h2>
            <p className="mt-2 text-xs leading-5 text-slate-500">
              {description}
            </p>

            <button className="mt-5 w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-bold hover:border-blue-300">
              Configure
            </button>
          </article>
        ))}
      </section>

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-bold">Delivery schedule</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-3">
          <label className="text-sm font-semibold">
            Daily summary
            <select className="mt-2 w-full rounded-xl border border-slate-200 bg-white p-3 font-normal">
              <option>08:00</option>
              <option>09:00</option>
              <option>18:00</option>
            </select>
          </label>

          <label className="text-sm font-semibold">
            Timezone
            <select className="mt-2 w-full rounded-xl border border-slate-200 bg-white p-3 font-normal">
              <option>Workspace timezone</option>
              <option>UTC</option>
            </select>
          </label>

          <label className="text-sm font-semibold">
            Critical alerts
            <select className="mt-2 w-full rounded-xl border border-slate-200 bg-white p-3 font-normal">
              <option>Immediately</option>
              <option>Hourly digest</option>
            </select>
          </label>
        </div>
      </section>
    </div>
  );
}

function BillingPage() {
  const plans = [
    {
      name: "Starter",
      price: "$199",
      description: "One platform and one advertising account",
      featured: false,
    },
    {
      name: "Growth",
      price: "$599",
      description: "All platforms with full autonomous optimization",
      featured: true,
    },
    {
      name: "Scale",
      price: "Custom",
      description: "Multiple organizations, accounts and advanced controls",
      featured: false,
    },
  ];

  return (
    <div className="mx-auto max-w-[1600px] space-y-7">
      <PageHeader
        eyebrow="Whop subscriptions"
        title="Plan and Billing"
        description="Subscription status, usage limits and feature entitlements will be synchronized from Whop."
        icon={CreditCard}
      />

      <section className="rounded-[1.75rem] border border-amber-200 bg-amber-50 p-5">
        <div className="flex items-start gap-3">
          <TriangleAlert size={20} className="mt-0.5 text-amber-700" />
          <div>
            <p className="font-bold text-amber-900">
              Development account has no active Whop subscription
            </p>
            <p className="mt-1 text-sm text-amber-700">
              Autonomous platform mutations remain blocked.
            </p>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        {plans.map((plan) => (
          <article
            key={plan.name}
            className={`rounded-[1.75rem] border p-6 shadow-sm ${
              plan.featured
                ? "border-blue-500 bg-[#1468F3] text-white"
                : "border-slate-200 bg-white"
            }`}
          >
            <StatusBadge
              label={plan.featured ? "Recommended" : "Available"}
              color={plan.featured ? "violet" : "slate"}
            />
            <h2 className="mt-6 text-2xl font-black">{plan.name}</h2>
            <p className="mt-3 text-4xl font-black">
              {plan.price}
              {plan.price.startsWith("$") && (
                <span className="text-sm font-normal opacity-60">/month</span>
              )}
            </p>
            <p className="mt-4 min-h-12 text-sm leading-6 opacity-70">
              {plan.description}
            </p>
            <button
              className={`mt-6 w-full rounded-xl px-5 py-3 text-sm font-bold ${
                plan.featured
                  ? "bg-white text-slate-950"
                  : "bg-[#1468F3] text-white"
              }`}
            >
              Select on Whop
            </button>
          </article>
        ))}
      </section>
    </div>
  );
}

function SettingsPage() {
  return (
    <div className="mx-auto max-w-[1600px] space-y-7">
      <PageHeader
        eyebrow="Workspace control"
        title="Business and Risk Settings"
        description="Define the business truth, profitability targets and immutable limits governing autonomous execution."
        icon={Settings}
      />

      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <article className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-bold">Business profile</h2>

          <div className="mt-6 grid gap-5 md:grid-cols-2">
            {[
              ["Business name", "Example Company"],
              ["Website", "https://example.com"],
              ["Currency", "USD"],
              ["Target CPA", "30.00"],
              ["Minimum ROAS", "3.00"],
              ["Gross margin", "70%"],
            ].map(([label, placeholder]) => (
              <label key={label} className="text-sm font-semibold">
                {label}
                <input
                  placeholder={placeholder}
                  className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none transition focus:border-blue-500"
                />
              </label>
            ))}
          </div>

          <button className="mt-6 rounded-xl bg-[#1468F3] px-5 py-3 text-sm font-bold text-white">
            Save business profile
          </button>
        </article>

        <article className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
          <ShieldCheck size={23} className="text-emerald-600" />
          <h2 className="mt-5 font-bold">Capital protection</h2>

          <div className="mt-5 space-y-4">
            <label className="block text-sm font-semibold">
              Maximum daily spend
              <input
                placeholder="$500"
                className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal"
              />
            </label>

            <label className="block text-sm font-semibold">
              Maximum monthly spend
              <input
                placeholder="$10,000"
                className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal"
              />
            </label>

            <label className="block text-sm font-semibold">
              Risk profile
              <select className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 font-normal">
                <option>Conservative</option>
                <option>Balanced</option>
                <option>Aggressive</option>
              </select>
            </label>
          </div>
        </article>
      </section>
    </div>
  );
}

export function SectionRouter({ section }: { section: string }) {
  switch (section) {
    case "connections":
      return <ConnectionsPage />;
    case "campaigns":
      return <CampaignsPage />;
    case "agents":
      return <AgentsPage />;
    case "decisions":
      return <DecisionsPage />;
    case "experiments":
      return <ExperimentsPage />;
    case "creative":
      return <CreativePage />;
    case "reports":
      return <ReportsPage />;
    case "notifications":
      return <NotificationsPage />;
    case "billing":
      return <BillingPage />;
    case "settings":
      return <SettingsPage />;
    default:
      return null;
  }
}
