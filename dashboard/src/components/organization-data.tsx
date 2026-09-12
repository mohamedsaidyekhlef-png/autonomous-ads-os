"use client";

import { AlertTriangle, Database, LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";

const API_URL =
  process.env.NODE_ENV === "production"
    ? "/api"
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080");

const titles = {
  campaigns: "Campaign drafts",
  decisions: "Decision journal",
  experiments: "Experiment laboratory",
  creative: "Creative lab",
  reports: "Executive reports",
  settings: "Workspace settings",
} as const;

type OrganizationResource = keyof typeof titles;
type OrganizationRecord = Record<string, unknown>;

function resourceEndpoint(resource: OrganizationResource): string {
  return resource === "creative" ? "creatives" : resource;
}

function recordTitle(item: OrganizationRecord): string {
  return String(
    item.name ??
      item.key ??
      item.objective ??
      item.report_type ??
      "Untitled record",
  );
}

function recordDescription(item: OrganizationRecord): string {
  return String(
    item.status ?? item.rationale ?? item.summary ?? "Saved shadow-mode record",
  );
}

function isOrganizationRecordArray(
  value: unknown,
): value is OrganizationRecord[] {
  return (
    Array.isArray(value) &&
    value.every(
      (item) =>
        typeof item === "object" && item !== null && !Array.isArray(item),
    )
  );
}

export function OrganizationData({
  resource,
}: {
  resource: OrganizationResource;
}) {
  const [items, setItems] = useState<OrganizationRecord[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadData() {
      setItems(null);
      setError("");

      try {
        const endpoint = resourceEndpoint(resource);
        const response = await fetch(`${API_URL}/v1/${endpoint}`, {
          signal: controller.signal,
          headers: {
            Accept: "application/json",
          },
        });

        const contentType = response.headers.get("content-type") ?? "";

        if (!response.ok) {
          throw new Error(
            "Data is unavailable until an authorized organization is selected.",
          );
        }

        if (!contentType.includes("application/json")) {
          throw new Error("The data endpoint returned an invalid response.");
        }

        const payload: unknown = await response.json();

        if (!isOrganizationRecordArray(payload)) {
          throw new Error("The data endpoint returned an unexpected format.");
        }

        setItems(payload);
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }

        setError(
          caught instanceof Error
            ? caught.message
            : "Unable to load organization data.",
        );
      }
    }

    void loadData();

    return () => {
      controller.abort();
    };
  }, [resource]);

  return (
    <div className="mx-auto max-w-[1600px] space-y-7">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-600">
          Organization data
        </p>

        <h1 className="mt-1 text-3xl font-black tracking-tight text-slate-950">
          {titles[resource]}
        </h1>

        <p className="mt-2 text-sm text-slate-500">
          Persisted, organization-isolated Shadow Mode records. Live platform
          actions are unavailable.
        </p>
      </header>

      <section
        aria-busy={items === null && !error}
        className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm"
      >
        {error ? (
          <div
            role="alert"
            className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700"
          >
            <AlertTriangle className="mt-0.5 shrink-0" size={18} />
            <span>{error}</span>
          </div>
        ) : items === null ? (
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <LoaderCircle className="animate-spin text-[#1468F3]" size={20} />
            Loading organization data…
          </div>
        ) : items.length === 0 ? (
          <div className="flex items-center gap-3 rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">
            <Database className="shrink-0" size={20} />
            <span>No saved {resource} records yet.</span>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((item, index) => {
              const key = String(item.id ?? item.key ?? `${resource}-${index}`);

              return (
                <article
                  key={key}
                  className="rounded-2xl border border-slate-200 p-4"
                >
                  <p className="font-bold text-slate-950">
                    {recordTitle(item)}
                  </p>

                  <p className="mt-1 text-sm text-slate-600">
                    {recordDescription(item)}
                  </p>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
