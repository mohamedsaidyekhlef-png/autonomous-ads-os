"use client";

import {
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  KeyRound,
  Link2,
  LockKeyhole,
  Search,
  ShieldCheck,
  Smartphone,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";
import type { IconType } from "react-icons";
import { FaSalesforce, FaSlack } from "react-icons/fa6";
import {
  SiGoogleads,
  SiGoogleanalytics,
  SiGooglesearchconsole,
  SiHubspot,
  SiMeta,
  SiShopify,
  SiStripe,
  SiTelegram,
  SiTiktok,
  SiWhatsapp,
  SiWoocommerce,
  SiZapier,
} from "react-icons/si";

type Category =
  | "Advertising"
  | "Analytics"
  | "Commerce"
  | "CRM"
  | "Notifications"
  | "Automation";

type Integration = {
  id: string;
  name: string;
  description: string;
  category: Category;
  icon: IconType;
  color: string;
  authorization: string;
  status: "available" | "coming_soon";
};

const integrations: Integration[] = [
  {
    id: "google-ads",
    name: "Google Ads",
    description:
      "Manage Search, Shopping, YouTube and Performance Max campaigns.",
    category: "Advertising",
    icon: SiGoogleads,
    color: "#4285F4",
    authorization: "Google OAuth 2.0",
    status: "available",
  },
  {
    id: "meta-ads",
    name: "Meta Ads",
    description:
      "Manage Facebook and Instagram campaigns, audiences and creatives.",
    category: "Advertising",
    icon: SiMeta,
    color: "#0866FF",
    authorization: "Meta Business OAuth",
    status: "coming_soon",
  },
  {
    id: "tiktok-ads",
    name: "TikTok Ads",
    description:
      "Manage TikTok campaigns, creatives, audiences and reporting.",
    category: "Advertising",
    icon: SiTiktok,
    color: "#000000",
    authorization: "TikTok Business OAuth",
    status: "coming_soon",
  },
  {
    id: "search-console",
    name: "Google Search Console",
    description:
      "Import organic search demand and landing-page performance.",
    category: "Analytics",
    icon: SiGooglesearchconsole,
    color: "#458CF5",
    authorization: "Google OAuth 2.0",
    status: "coming_soon",
  },
  {
    id: "google-analytics",
    name: "Google Analytics",
    description:
      "Import website sessions, conversions and attribution signals.",
    category: "Analytics",
    icon: SiGoogleanalytics,
    color: "#E37400",
    authorization: "Google OAuth 2.0",
    status: "coming_soon",
  },
  {
    id: "shopify",
    name: "Shopify",
    description:
      "Synchronize products, orders, revenue, customers and inventory.",
    category: "Commerce",
    icon: SiShopify,
    color: "#7AB55C",
    authorization: "Shopify OAuth",
    status: "coming_soon",
  },
  {
    id: "woocommerce",
    name: "WooCommerce",
    description:
      "Synchronize store revenue, products, orders and customer data.",
    category: "Commerce",
    icon: SiWoocommerce,
    color: "#96588A",
    authorization: "WooCommerce REST API",
    status: "coming_soon",
  },
  {
    id: "stripe",
    name: "Stripe",
    description:
      "Use verified payments and revenue for profitability reporting.",
    category: "Commerce",
    icon: SiStripe,
    color: "#635BFF",
    authorization: "Stripe OAuth",
    status: "coming_soon",
  },
  {
    id: "hubspot",
    name: "HubSpot",
    description:
      "Import leads, lifecycle stages, qualified opportunities and sales.",
    category: "CRM",
    icon: SiHubspot,
    color: "#FF7A59",
    authorization: "HubSpot OAuth",
    status: "coming_soon",
  },
  {
    id: "salesforce",
    name: "Salesforce",
    description:
      "Connect advertising activity to qualified leads and closed revenue.",
    category: "CRM",
    icon: FaSalesforce,
    color: "#00A1E0",
    authorization: "Salesforce OAuth",
    status: "coming_soon",
  },
  {
    id: "slack",
    name: "Slack",
    description:
      "Send daily summaries, agent decisions and critical alerts.",
    category: "Notifications",
    icon: FaSlack,
    color: "#4A154B",
    authorization: "Slack OAuth",
    status: "coming_soon",
  },
  {
    id: "telegram",
    name: "Telegram",
    description:
      "Receive performance summaries and urgent alerts through a bot.",
    category: "Notifications",
    icon: SiTelegram,
    color: "#26A5E4",
    authorization: "Telegram Bot",
    status: "coming_soon",
  },
  {
    id: "whatsapp",
    name: "WhatsApp",
    description:
      "Receive approved business summaries and important notifications.",
    category: "Notifications",
    icon: SiWhatsapp,
    color: "#25D366",
    authorization: "WhatsApp Cloud API",
    status: "coming_soon",
  },
  {
    id: "zapier",
    name: "Zapier",
    description:
      "Trigger external workflows from decisions, alerts and outcomes.",
    category: "Automation",
    icon: SiZapier,
    color: "#FF4F00",
    authorization: "Zapier App",
    status: "coming_soon",
  },
];

const categories = [
  "All",
  "Advertising",
  "Analytics",
  "Commerce",
  "CRM",
  "Notifications",
  "Automation",
] as const;

export default function ConnectionsPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<(typeof categories)[number]>("All");
  const [selected, setSelected] = useState<Integration | null>(null);

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();

    return integrations.filter((integration) => {
      const categoryMatches =
        category === "All" || integration.category === category;

      const searchMatches =
        !query ||
        integration.name.toLowerCase().includes(query) ||
        integration.description.toLowerCase().includes(query);

      return categoryMatches && searchMatches;
    });
  }, [category, search]);

  return (
    <div className="mx-auto max-w-[1600px] space-y-7">
      <header className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-gradient-to-br from-[#1468F3] to-[#1468F3] p-3 text-white shadow-lg shadow-blue-200">
            <Link2 size={25} />
          </div>

          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-600">
              Integration marketplace
            </p>
            <h1 className="mt-1 text-3xl font-black tracking-tight">
              Connect your business stack
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
              Securely connect advertising, analytics, commerce, CRM and
              notification platforms. Customers authorize access using each
              platform&apos;s official login page.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-xs font-bold text-emerald-700">
          <ShieldCheck size={16} />
          Encrypted OAuth vault
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-50 p-2.5 text-blue-600">
              <Link2 size={19} />
            </div>
            <div>
              <p className="text-2xl font-black">0</p>
              <p className="text-xs text-slate-500">Connected services</p>
            </div>
          </div>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-50 p-2.5 text-emerald-600">
              <LockKeyhole size={19} />
            </div>
            <div>
              <p className="text-2xl font-black">Encrypted</p>
              <p className="text-xs text-slate-500">Credential storage</p>
            </div>
          </div>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-50 p-2.5 text-blue-600">
              <Smartphone size={19} />
            </div>
            <div>
              <p className="text-2xl font-black">Responsive</p>
              <p className="text-xs text-slate-500">Desktop and mobile</p>
            </div>
          </div>
        </article>
      </section>

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="relative w-full max-w-lg">
            <Search
              size={18}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search integrations"
              className="w-full rounded-xl border border-slate-200 py-3 pl-11 pr-4 text-sm outline-none transition focus:border-blue-500"
            />
          </div>

          <div className="flex gap-2 overflow-x-auto pb-1">
            {categories.map((item) => (
              <button
                key={item}
                onClick={() => setCategory(item)}
                className={`whitespace-nowrap rounded-xl px-4 py-2.5 text-xs font-bold transition ${
                  category === item
                    ? "bg-[#1468F3] text-white"
                    : "border border-slate-200 bg-white text-slate-600 hover:border-blue-300"
                }`}
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {filtered.map((integration) => {
          const Icon = integration.icon;

          return (
            <article
              key={integration.id}
              className="group rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:border-blue-300 hover:shadow-lg"
            >
              <div className="flex items-start justify-between">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-slate-100 bg-white shadow-sm">
                  <Icon
                    size={30}
                    style={{ color: integration.color }}
                    title={integration.name}
                  />
                </div>

                <span
                  className={`rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase ${
                    integration.status === "available"
                      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                      : "border-slate-200 bg-slate-50 text-slate-500"
                  }`}
                >
                  {integration.status === "available"
                    ? "Available"
                    : "Coming soon"}
                </span>
              </div>

              <h2 className="mt-5 text-lg font-bold">{integration.name}</h2>

              <p className="mt-2 min-h-12 text-sm leading-6 text-slate-500">
                {integration.description}
              </p>

              <div className="mt-5 flex items-center gap-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
                <KeyRound size={14} />
                {integration.authorization}
              </div>

              <button
                disabled={integration.status !== "available"}
                onClick={() => setSelected(integration)}
                className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-[#1468F3] px-4 py-3 text-sm font-bold text-white transition enabled:hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-500"
              >
                {integration.status === "available"
                  ? `Connect ${integration.name}`
                  : "Coming soon"}
                {integration.status === "available" && (
                  <ChevronRight size={16} />
                )}
              </button>
            </article>
          );
        })}
      </section>

      {selected && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#1468F3]/70 p-4 backdrop-blur-sm">
          <button
            aria-label="Close dialog"
            className="absolute inset-0"
            onClick={() => setSelected(null)}
          />

          <article className="relative z-10 w-full max-w-lg rounded-[2rem] bg-white p-7 shadow-2xl">
            <button
              aria-label="Close"
              onClick={() => setSelected(null)}
              className="absolute right-5 top-5 rounded-xl p-2 text-slate-400 hover:bg-slate-100"
            >
              <X size={19} />
            </button>

            <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-slate-100 shadow-sm">
              <selected.icon
                size={34}
                style={{ color: selected.color }}
                title={selected.name}
              />
            </div>

            <h2 className="mt-6 text-2xl font-black">
              Connect {selected.name}
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-500">
              You will be redirected to {selected.name}&apos;s official
              authorization page. Autonomous Ads will never receive your
              password.
            </p>

            <div className="mt-5 space-y-3 rounded-2xl bg-slate-50 p-4">
              {[
                "Official OAuth authorization",
                "Encrypted token storage",
                "Organization-isolated access",
                "Revoke access at any time",
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-center gap-3 text-sm text-slate-700"
                >
                  <CheckCircle2 size={16} className="text-emerald-600" />
                  {item}
                </div>
              ))}
            </div>

            <a href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080"}/oauth/google/start`} className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-[#FF6500] px-5 py-3.5 font-bold text-white transition hover:bg-[#E85B00]">
              Continue to {selected.name}
              <ExternalLink size={17} />
            </a>

            <p className="mt-4 text-center text-xs text-amber-700">
              Only Google Ads OAuth is available in Shadow Beta. All unsupported integrations are marked Coming soon.
            </p>
          </article>
        </div>
      )}
    </div>
  );
}
