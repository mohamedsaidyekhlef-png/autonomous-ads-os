"use client";

import {
  CheckCircle2,
  Clock3,
  FlaskConical,
  Pause,
  Play,
  Plus,
  ShieldCheck,
  Trash2,
  X,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

type ExperimentStatus = "draft" | "running" | "paused" | "completed";

type Experiment = {
  id: string;
  name: string;
  hypothesis: string;
  primaryMetric: string;
  status: ExperimentStatus;
  createdAt: string;
};

const STORAGE_KEY = "autonomous-ads-os:experiments:v1";

function isExperiment(value: unknown): value is Experiment {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const item = value as Record<string, unknown>;

  return (
    typeof item.id === "string" &&
    typeof item.name === "string" &&
    typeof item.hypothesis === "string" &&
    typeof item.primaryMetric === "string" &&
    typeof item.status === "string" &&
    ["draft", "running", "paused", "completed"].includes(item.status) &&
    typeof item.createdAt === "string"
  );
}

function loadExperiments(): Experiment[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);

    if (!raw) {
      return [];
    }

    const parsed: unknown = JSON.parse(raw);

    return Array.isArray(parsed) ? parsed.filter(isExperiment) : [];
  } catch {
    return [];
  }
}

function statusStyle(status: ExperimentStatus): string {
  switch (status) {
    case "running":
      return "border-blue-200 bg-blue-50 text-blue-700";
    case "completed":
      return "border-emerald-200 bg-emerald-50 text-emerald-700";
    case "paused":
      return "border-amber-200 bg-amber-50 text-amber-700";
    default:
      return "border-slate-200 bg-slate-50 text-slate-600";
  }
}

export function ExperimentsWorkspace() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [name, setName] = useState("");
  const [hypothesis, setHypothesis] = useState("");
  const [primaryMetric, setPrimaryMetric] = useState("");
  const [error, setError] = useState("");

  /* eslint-disable react-hooks/set-state-in-effect -- Hydrates state from browser-local storage. */
  useEffect(() => {
    setExperiments(loadExperiments());
    setLoaded(true);
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  useEffect(() => {
    if (!loaded) {
      return;
    }

    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(experiments));
  }, [experiments, loaded]);

  const counts = useMemo(
    () => ({
      running: experiments.filter((item) => item.status === "running").length,
      waiting: experiments.filter(
        (item) => item.status === "draft" || item.status === "paused",
      ).length,
      completed: experiments.filter((item) => item.status === "completed")
        .length,
    }),
    [experiments],
  );

  function createExperiment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (
      name.trim().length < 2 ||
      hypothesis.trim().length < 10 ||
      primaryMetric.trim().length < 2
    ) {
      setError(
        "Enter a name, a clear hypothesis, and a primary success metric.",
      );
      return;
    }

    const experiment: Experiment = {
      id: crypto.randomUUID(),
      name: name.trim(),
      hypothesis: hypothesis.trim(),
      primaryMetric: primaryMetric.trim(),
      status: "draft",
      createdAt: new Date().toISOString(),
    };

    setExperiments((current) => [experiment, ...current]);
    setName("");
    setHypothesis("");
    setPrimaryMetric("");
    setFormOpen(false);
  }

  function setStatus(id: string, status: ExperimentStatus) {
    setExperiments((current) =>
      current.map((item) => (item.id === id ? { ...item, status } : item)),
    );
  }

  function removeExperiment(id: string) {
    setExperiments((current) => current.filter((item) => item.id !== id));
  }

  return (
    <main className="mx-auto max-w-[1600px] space-y-7">
      <header className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-blue-600 p-3 text-white shadow-lg shadow-blue-200">
            <FlaskConical size={25} />
          </div>

          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-600">
              Controlled learning
            </p>
            <h1 className="mt-1 text-3xl font-black tracking-tight text-slate-950">
              Experiment Laboratory
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
              Design and track hypothesis-driven tests without changing live
              advertising accounts.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setFormOpen((current) => !current)}
          className="flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-bold text-white shadow-lg transition hover:bg-blue-700"
        >
          {formOpen ? <X size={17} /> : <Plus size={17} />}
          {formOpen ? "Close form" : "Design experiment"}
        </button>
      </header>

      <div className="flex items-center gap-2 rounded-2xl border border-violet-200 bg-violet-50 px-4 py-3 text-xs font-semibold text-violet-700">
        <ShieldCheck size={17} />
        Browser-local Shadow Mode — no advertising platform changes
      </div>

      {formOpen && (
        <form
          onSubmit={createExperiment}
          className="rounded-3xl border border-blue-200 bg-white p-6 shadow-sm"
        >
          <h2 className="text-xl font-black text-slate-950">New experiment</h2>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <label className="text-sm font-bold text-slate-700">
              Experiment name
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Landing page value proposition"
                className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-blue-500"
              />
            </label>

            <label className="text-sm font-bold text-slate-700">
              Primary metric
              <input
                value={primaryMetric}
                onChange={(event) => setPrimaryMetric(event.target.value)}
                placeholder="Conversion rate"
                className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-blue-500"
              />
            </label>

            <label className="text-sm font-bold text-slate-700 md:col-span-2">
              Hypothesis
              <textarea
                value={hypothesis}
                onChange={(event) => setHypothesis(event.target.value)}
                placeholder="If we clarify the primary benefit above the fold, conversion rate should improve because visitors will understand the offer sooner."
                rows={4}
                className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-blue-500"
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
            className="mt-5 flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-bold text-white hover:bg-blue-700"
          >
            <Plus size={17} />
            Save experiment draft
          </button>
        </form>
      )}

      <section className="grid gap-4 md:grid-cols-3">
        {[
          {
            label: "Active tests",
            value: counts.running,
            icon: FlaskConical,
            color: "text-blue-600",
          },
          {
            label: "Awaiting action",
            value: counts.waiting,
            icon: Clock3,
            color: "text-amber-600",
          },
          {
            label: "Completed learnings",
            value: counts.completed,
            icon: CheckCircle2,
            color: "text-emerald-600",
          },
        ].map(({ label, value, icon: Icon, color }) => (
          <article
            key={label}
            className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <Icon size={21} className={color} />
            <p className="mt-5 text-sm font-semibold text-slate-500">{label}</p>
            <p className="mt-2 text-4xl font-black text-slate-950">{value}</p>
          </article>
        ))}
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <h2 className="text-lg font-black text-slate-950">
            Experiment portfolio
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Drafts and status changes are stored in this browser.
          </p>
        </div>

        {!loaded ? (
          <p className="mt-6 text-sm text-slate-500">Loading experiments…</p>
        ) : experiments.length === 0 ? (
          <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center">
            <FlaskConical className="mx-auto text-slate-400" size={30} />
            <p className="mt-4 font-bold text-slate-900">
              No experiments designed
            </p>
            <p className="mt-2 text-sm text-slate-500">
              Create a hypothesis, select a metric, and save your first Shadow
              Mode experiment.
            </p>
          </div>
        ) : (
          <div className="mt-6 space-y-4">
            {experiments.map((experiment) => (
              <article
                key={experiment.id}
                className="rounded-2xl border border-slate-200 p-5"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-black text-slate-950">
                        {experiment.name}
                      </h3>
                      <span
                        className={`rounded-full border px-2.5 py-1 text-[10px] font-black uppercase ${statusStyle(experiment.status)}`}
                      >
                        {experiment.status}
                      </span>
                    </div>

                    <p className="mt-3 text-sm leading-6 text-slate-600">
                      {experiment.hypothesis}
                    </p>

                    <p className="mt-3 text-xs font-bold text-slate-500">
                      Primary metric: {experiment.primaryMetric}
                    </p>
                  </div>

                  <div className="flex shrink-0 flex-wrap gap-2">
                    {experiment.status !== "running" && (
                      <button
                        type="button"
                        onClick={() => setStatus(experiment.id, "running")}
                        className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white"
                      >
                        <Play size={15} />
                        Start
                      </button>
                    )}

                    {experiment.status === "running" && (
                      <button
                        type="button"
                        onClick={() => setStatus(experiment.id, "paused")}
                        className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 text-xs font-bold text-amber-700"
                      >
                        <Pause size={15} />
                        Pause
                      </button>
                    )}

                    {experiment.status !== "completed" && (
                      <button
                        type="button"
                        onClick={() => setStatus(experiment.id, "completed")}
                        className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-xs font-bold text-emerald-700"
                      >
                        <CheckCircle2 size={15} />
                        Complete
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={() => removeExperiment(experiment.id)}
                      aria-label={`Delete ${experiment.name}`}
                      title="Delete experiment"
                      className="rounded-xl border border-slate-200 p-2 text-slate-500 hover:border-red-200 hover:text-red-600"
                    >
                      <Trash2 size={17} />
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
