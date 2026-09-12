"use client";

import {
  CheckCircle2,
  FileText,
  Image as ImageIcon,
  Plus,
  ShieldCheck,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

type CreativeStatus = "brief" | "ready" | "archived";

type CreativeBrief = {
  id: string;
  name: string;
  platform: string;
  prompt: string;
  status: CreativeStatus;
  createdAt: string;
};

const STORAGE_KEY = "autonomous-ads-os:creative-briefs:v1";

function isCreativeBrief(value: unknown): value is CreativeBrief {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const item = value as Record<string, unknown>;

  return (
    typeof item.id === "string" &&
    typeof item.name === "string" &&
    typeof item.platform === "string" &&
    typeof item.prompt === "string" &&
    typeof item.status === "string" &&
    ["brief", "ready", "archived"].includes(item.status) &&
    typeof item.createdAt === "string"
  );
}

function loadBriefs(): CreativeBrief[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);

    if (!raw) {
      return [];
    }

    const parsed: unknown = JSON.parse(raw);

    return Array.isArray(parsed) ? parsed.filter(isCreativeBrief) : [];
  } catch {
    return [];
  }
}

export function CreativeLabWorkspace() {
  const [briefs, setBriefs] = useState<CreativeBrief[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [name, setName] = useState("");
  const [platform, setPlatform] = useState("Google Ads");
  const [prompt, setPrompt] = useState("");
  const [error, setError] = useState("");

  /* eslint-disable react-hooks/set-state-in-effect -- Hydrates state from browser-local storage. */
  useEffect(() => {
    setBriefs(loadBriefs());
    setLoaded(true);
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  useEffect(() => {
    if (!loaded) {
      return;
    }

    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(briefs));
  }, [briefs, loaded]);

  const counts = useMemo(
    () => ({
      briefs: briefs.filter((item) => item.status === "brief").length,
      ready: briefs.filter((item) => item.status === "ready").length,
      archived: briefs.filter((item) => item.status === "archived").length,
    }),
    [briefs],
  );

  function createBrief(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (name.trim().length < 2 || prompt.trim().length < 10) {
      setError("Enter a creative name and a brief of at least ten characters.");
      return;
    }

    const brief: CreativeBrief = {
      id: crypto.randomUUID(),
      name: name.trim(),
      platform,
      prompt: prompt.trim(),
      status: "brief",
      createdAt: new Date().toISOString(),
    };

    setBriefs((current) => [brief, ...current]);
    setName("");
    setPrompt("");
    setFormOpen(false);
  }

  function updateStatus(id: string, status: CreativeStatus) {
    setBriefs((current) =>
      current.map((item) => (item.id === id ? { ...item, status } : item)),
    );
  }

  function removeBrief(id: string) {
    setBriefs((current) => current.filter((item) => item.id !== id));
  }

  return (
    <main className="mx-auto max-w-[1600px] space-y-7">
      <header className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-violet-600 p-3 text-white shadow-lg shadow-violet-200">
            <Sparkles size={25} />
          </div>

          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-violet-600">
              Creative intelligence
            </p>
            <h1 className="mt-1 text-3xl font-black tracking-tight text-slate-950">
              Creative Lab
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
              Capture structured advertising briefs and move approved concepts
              through a protected Shadow Mode workflow.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setFormOpen((current) => !current)}
          className="flex items-center justify-center gap-2 rounded-xl bg-violet-600 px-5 py-3 text-sm font-bold text-white shadow-lg transition hover:bg-violet-700"
        >
          {formOpen ? <X size={17} /> : <Plus size={17} />}
          {formOpen ? "Close form" : "New creative brief"}
        </button>
      </header>

      <div className="flex items-center gap-2 rounded-2xl border border-violet-200 bg-violet-50 px-4 py-3 text-xs font-semibold text-violet-700">
        <ShieldCheck size={17} />
        Browser-local drafts — nothing is published to an advertising account
      </div>

      {formOpen && (
        <form
          onSubmit={createBrief}
          className="rounded-3xl border border-violet-200 bg-white p-6 shadow-sm"
        >
          <h2 className="text-xl font-black text-slate-950">
            Create creative brief
          </h2>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <label className="text-sm font-bold text-slate-700">
              Brief name
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="B2B accounting search launch"
                className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-violet-500"
              />
            </label>

            <label className="text-sm font-bold text-slate-700">
              Platform
              <select
                value={platform}
                onChange={(event) => setPlatform(event.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 font-normal outline-none focus:border-violet-500"
              >
                <option>Google Ads</option>
                <option>Meta Ads</option>
                <option>TikTok Ads</option>
                <option>Cross-platform</option>
              </select>
            </label>

            <label className="text-sm font-bold text-slate-700 md:col-span-2">
              Creative direction
              <textarea
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder="Describe the audience, customer problem, offer, proof, objections, desired tone, and call to action."
                rows={5}
                className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-violet-500"
              />
            </label>
          </div>

          {error && (
            <p
              role="alert"
              className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            className="mt-5 flex items-center gap-2 rounded-xl bg-violet-600 px-5 py-3 text-sm font-bold text-white hover:bg-violet-700"
          >
            <FileText size={17} />
            Save brief
          </button>
        </form>
      )}

      <section className="grid gap-4 md:grid-cols-3">
        {[
          ["Draft briefs", counts.briefs, FileText, "text-violet-600"],
          ["Ready for review", counts.ready, CheckCircle2, "text-emerald-600"],
          ["Archived", counts.archived, ImageIcon, "text-slate-500"],
        ].map(([label, value, RawIcon, color]) => {
          const Icon = RawIcon as typeof FileText;

          return (
            <article
              key={String(label)}
              className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <Icon size={21} className={String(color)} />
              <p className="mt-5 text-sm font-semibold text-slate-500">
                {String(label)}
              </p>
              <p className="mt-2 text-4xl font-black text-slate-950">
                {String(value)}
              </p>
            </article>
          );
        })}
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-black text-slate-950">
          Creative portfolio
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Briefs are stored in this browser until the production API is
          connected.
        </p>

        {!loaded ? (
          <p className="mt-6 text-sm text-slate-500">
            Loading creative briefs…
          </p>
        ) : briefs.length === 0 ? (
          <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center">
            <Sparkles className="mx-auto text-slate-400" size={30} />
            <p className="mt-4 font-bold text-slate-900">
              Creative portfolio is empty
            </p>
            <p className="mt-2 text-sm text-slate-500">
              Create a structured brief to begin the Shadow Mode creative
              workflow.
            </p>
          </div>
        ) : (
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {briefs.map((brief) => (
              <article
                key={brief.id}
                className="rounded-2xl border border-slate-200 p-5"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-black text-slate-950">
                        {brief.name}
                      </h3>
                      <span className="rounded-full border border-violet-200 bg-violet-50 px-2.5 py-1 text-[10px] font-black uppercase text-violet-700">
                        {brief.status}
                      </span>
                    </div>
                    <p className="mt-2 text-xs font-bold text-slate-500">
                      {brief.platform}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => removeBrief(brief.id)}
                    aria-label={`Delete ${brief.name}`}
                    title="Delete brief"
                    className="rounded-xl border border-slate-200 p-2 text-slate-500 hover:border-red-200 hover:text-red-600"
                  >
                    <Trash2 size={17} />
                  </button>
                </div>

                <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-slate-600">
                  {brief.prompt}
                </p>

                <div className="mt-5 flex flex-wrap gap-2">
                  {brief.status === "brief" && (
                    <button
                      type="button"
                      onClick={() => updateStatus(brief.id, "ready")}
                      className="flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2 text-xs font-bold text-white"
                    >
                      <CheckCircle2 size={15} />
                      Mark ready
                    </button>
                  )}

                  {brief.status !== "archived" && (
                    <button
                      type="button"
                      onClick={() => updateStatus(brief.id, "archived")}
                      className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600"
                    >
                      Archive
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
