"use client";

import { Activity, Cpu, Database, Radio } from "lucide-react";
import { useEffect, useState } from "react";

type Service = {
  status?: string;
  selected_model?: string;
  model_available?: boolean;
};

type Readiness = {
  status: string;
  dry_run: boolean;
  checks: {
    database?: Service;
    redis?: Service;
    ollama?: Service;
  };
};

const services = [
  {
    key: "database",
    label: "PostgreSQL",
    description: "Tenant and decision storage",
    icon: Database,
  },
  {
    key: "redis",
    label: "Redis",
    description: "Jobs, locks and live state",
    icon: Radio,
  },
  {
    key: "ollama",
    label: "Qwen Intelligence",
    description: "Local reasoning service",
    icon: Cpu,
  },
] as const;

export function SystemStatus() {
  const [data, setData] = useState<Readiness | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const api =
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";

    async function refresh() {
      try {
        const response = await fetch(`${api}/ready`);
        const payload = (await response.json()) as Readiness;

        setData(payload);
        setError(false);
      } catch {
        setError(true);
      }
    }

    void refresh();
    const interval = window.setInterval(refresh, 15000);

    return () => window.clearInterval(interval);
  }, []);

  return (
    <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="font-bold">System intelligence</h2>
          <p className="mt-1 text-xs text-slate-500">
            Live operational dependencies
          </p>
        </div>

        <Activity
          size={20}
          className={error ? "text-red-500" : "text-emerald-500"}
        />
      </div>

      <div className="space-y-3">
        {services.map(({ key, label, description, icon: Icon }) => {
          const service = data?.checks[key];
          const healthy = service?.status === "healthy";

          return (
            <div
              key={key}
              className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-slate-50/80 p-3.5"
            >
              <div className="rounded-xl bg-white p-2 text-slate-600 shadow-sm">
                <Icon size={17} />
              </div>

              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold">{label}</p>
                <p className="truncate text-xs text-slate-500">
                  {description}
                </p>
              </div>

              <div
                className={`h-2.5 w-2.5 rounded-full ${
                  healthy ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
            </div>
          );
        })}
      </div>

      <div className="mt-4 rounded-xl bg-[#1468F3] px-4 py-3 text-xs text-slate-300">
        Mode:{" "}
        <span className="font-bold text-amber-300">
          {data?.dry_run === false ? "LIVE" : "DRY RUN"}
        </span>
      </div>
    </section>
  );
}
