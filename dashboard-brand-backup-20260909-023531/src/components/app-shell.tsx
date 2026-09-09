"use client";

import {
  Activity,
  BarChart3,
  Bell,
  Bot,
  CreditCard,
  FlaskConical,
  LayoutDashboard,
  Link2,
  Megaphone,
  Menu,
  Settings,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useState } from "react";

type NavigationItem = {
  name: string;
  href: string;
  icon: LucideIcon;
};

const navigation: NavigationItem[] = [
  { name: "Overview", href: "/overview", icon: LayoutDashboard },
  { name: "Connections", href: "/connections", icon: Link2 },
  { name: "Campaigns", href: "/campaigns", icon: Megaphone },
  { name: "AI Agent Team", href: "/agents", icon: Bot },
  { name: "Decisions", href: "/decisions", icon: Activity },
  { name: "Experiments", href: "/experiments", icon: FlaskConical },
  { name: "Creative Lab", href: "/creative", icon: Sparkles },
  { name: "Reports", href: "/reports", icon: BarChart3 },
  { name: "Notifications", href: "/notifications", icon: Bell },
  { name: "Billing", href: "/billing", icon: CreditCard },
  { name: "Settings", href: "/settings", icon: Settings },
];

function SidebarContent({
  pathname,
  close,
}: {
  pathname: string;
  close?: () => void;
}) {
  return (
    <>
      <div className="flex h-20 items-center gap-3 border-b border-white/10 px-5">
        <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-2xl border border-white/10 bg-white shadow-lg shadow-blue-950">
          <Image
            src="/brand-logo.png"
            alt="Autonomous Ads"
            fill
            priority
            sizes="48px"
            className="object-cover"
          />
          <span className="absolute bottom-1 right-1 h-2.5 w-2.5 rounded-full border-2 border-slate-950 bg-emerald-400" />
        </div>

        <div>
          <p className="font-bold tracking-tight">Autonomous Ads</p>
          <p className="text-xs text-slate-400">Intelligence Command</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        <p className="px-3 pb-2 pt-2 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-600">
          Workspace
        </p>

        {navigation.map((item) => {
          const Icon = item.icon;
          const active =
            pathname === item.href ||
            pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={close}
              className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                active
                  ? "bg-gradient-to-r from-[#1468F3] to-[#13C7E7] text-white shadow-lg shadow-blue-950/40"
                  : "text-slate-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon
                size={18}
                className={
                  active
                    ? "text-white"
                    : "text-slate-500 group-hover:text-blue-400"
                }
              />
              <span>{item.name}</span>

              {item.name === "Notifications" && (
                <span className="ml-auto rounded-full bg-rose-500 px-2 py-0.5 text-[10px] font-bold text-white">
                  0
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="m-3 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-emerald-300">
          <ShieldCheck size={17} />
          Capital protection active
        </div>
        <p className="mt-2 text-xs leading-5 text-slate-500">
          Execution remains in dry-run mode until subscription, account access
          and spending limits are validated.
        </p>
      </div>

      <div className="border-t border-white/10 p-4">
        <div className="flex items-center gap-3 rounded-xl p-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 text-xs font-black">
            LV
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold">Development Admin</p>
            <p className="truncate text-xs text-slate-500">
              Whop subscription pending
            </p>
          </div>
        </div>
      </div>
    </>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#f4f6fb]">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 flex-col border-r border-slate-800 bg-[#070b17] text-white md:flex">
        <SidebarContent pathname={pathname} />
      </aside>

      {mobileOpen && (
        <>
          <button
            aria-label="Close navigation overlay"
            onClick={() => setMobileOpen(false)}
            className="fixed inset-0 z-40 bg-slate-950/70 backdrop-blur-sm md:hidden"
          />

          <aside className="fixed inset-y-0 left-0 z-50 flex w-[86%] max-w-72 flex-col bg-[#070b17] text-white shadow-2xl md:hidden">
            <button
              aria-label="Close navigation"
              onClick={() => setMobileOpen(false)}
              className="absolute right-3 top-5 rounded-lg p-2 text-slate-400 hover:bg-white/10 hover:text-white"
            >
              <X size={20} />
            </button>

            <SidebarContent
              pathname={pathname}
              close={() => setMobileOpen(false)}
            />
          </aside>
        </>
      )}

      <div className="md:pl-72">
        <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur-xl sm:px-6">
          <div className="flex items-center gap-3">
            <button
              aria-label="Open navigation"
              onClick={() => setMobileOpen(true)}
              className="rounded-xl border border-slate-200 bg-white p-2.5 shadow-sm md:hidden"
            >
              <Menu size={20} />
            </button>

            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-600">
                Performance Intelligence
              </p>
              <p className="text-sm text-slate-500">
                Autonomous operations workspace
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button className="relative rounded-xl border border-slate-200 bg-white p-2.5 text-slate-500 shadow-sm transition hover:text-slate-950">
              <Bell size={19} />
            </button>

            <div className="hidden items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-bold text-emerald-700 sm:flex">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              Core online
            </div>
          </div>
        </header>

        <main className="min-h-[calc(100vh-5rem)] p-4 sm:p-6 xl:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
