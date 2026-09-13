"use client";

import { useRef, useState } from "react";
import {
  AlertTriangle,
  BadgeCheck,
  Brain,
  CheckCircle2,
  ClipboardCheck,
  FileKey2,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  XCircle,
} from "lucide-react";

const API_URL =
  process.env.NODE_ENV === "production"
    ? "/api"
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080");

const metricDefinitions = [
  { key: "impressions", label: "Impressions", step: "1" },
  { key: "clicks", label: "Clicks", step: "1" },
  { key: "spend", label: "Spend", step: "0.01" },
  { key: "conversions", label: "Conversions", step: "0.01" },
  { key: "revenue", label: "Revenue", step: "0.01" },
] as const;

type MetricName = (typeof metricDefinitions)[number]["key"];
type ReviewDecision = "approved" | "rejected" | "revision_required";

type ValidationIssue = {
  code: string;
  level: "warning" | "error";
  message: string;
  path: string;
};

type Finding = {
  title: string;
  observation: string;
  significance: string;
  severity: "info" | "low" | "medium" | "high" | "critical";
  basis: string;
  evidence_ids: string[];
  confidence: number;
  limitations: string[];
};

type Recommendation = {
  title: string;
  rationale: string;
  expected_impact: string;
  measurement_plan: string;
  risk: "info" | "low" | "medium" | "high" | "critical";
  confidence: number;
  evidence_ids: string[];
  reversible: boolean;
  requires_human_approval: boolean;
};

type SpecialistAssessment = {
  agent_id: string;
  role_name: string;
  findings: Finding[];
  recommendations: Recommendation[];
  missing_information: string[];
  conflicts: string[];
};

type ExpertReport = {
  run_id: string;
  rubric_version: string;
  mode: "shadow";
  executive_summary: string;
  data_quality_score: number;
  specialist_assessments: SpecialistAssessment[];
  prioritized_recommendations: Recommendation[];
  assumptions: string[];
  missing_information: string[];
  contradictions: string[];
  execution_requested: boolean;
  automated_validation_passed: boolean;
  created_at: string;
};

type HumanReview = {
  id: string;
  decision: ReviewDecision;
  reviewer_identity: string;
  reviewer_role: string;
  comments: string;
  report_hash: string;
  rubric_version: string;
  reviewed_at: string;
};

type ExpertReviewRun = {
  run_id: string;
  status: string;
  mode: string;
  analysis_engine: string;
  objective: string;
  report: ExpertReport | null;
  validation: {
    passed: boolean;
    issues: ValidationIssue[];
    checked_at?: string;
  } | null;
  report_hash: string | null;
  rubric_version: string | null;
  review_required: boolean;
  review_label: string;
  human_review: HumanReview | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  links: {
    self: string;
    review: string;
  };
  idempotent: boolean;
};

type ApiError = {
  detail?: string;
};

const initialMetrics: Record<MetricName, string> = {
  impressions: "",
  clicks: "",
  spend: "",
  conversions: "",
  revenue: "",
};

function createIdempotencyKey(prefix: string) {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}-${crypto.randomUUID()}`;
  }

  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function readResponse<T extends object>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type") ?? "";

  if (!contentType.includes("application/json")) {
    throw new Error("The API returned an invalid response.");
  }

  const payload = (await response.json()) as T | ApiError;

  if (!response.ok) {
    const message =
      "detail" in payload && typeof payload.detail === "string"
        ? payload.detail
        : "The expert-review request failed.";

    throw new Error(message);
  }

  return payload as T;
}

function statusClasses(status: string) {
  if (status === "completed") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }

  if (status === "awaiting_human_review") {
    return "border-amber-200 bg-amber-50 text-amber-700";
  }

  if (
    status === "rejected" ||
    status === "failed" ||
    status.startsWith("failed_")
  ) {
    return "border-red-200 bg-red-50 text-red-700";
  }

  if (status === "revision_required") {
    return "border-orange-200 bg-orange-50 text-orange-700";
  }

  return "border-blue-200 bg-blue-50 text-blue-700";
}

function severityClasses(severity: Finding["severity"]) {
  if (severity === "critical" || severity === "high") {
    return "border-red-200 bg-red-50 text-red-700";
  }

  if (severity === "medium") {
    return "border-amber-200 bg-amber-50 text-amber-700";
  }

  if (severity === "low") {
    return "border-blue-200 bg-blue-50 text-blue-700";
  }

  return "border-slate-200 bg-slate-50 text-slate-600";
}

function percentage(value: number) {
  return `${Math.round(value * 100)}%`;
}

function formatDate(value: string | null) {
  if (!value) return "Not completed";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat("en-US", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(date);
}

export function ExpertReviewWorkspace() {
  const [objective, setObjective] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [metrics, setMetrics] =
    useState<Record<MetricName, string>>(initialMetrics);
  const [assumptions, setAssumptions] = useState("");
  const [run, setRun] = useState<ExpertReviewRun | null>(null);
  const [lookupId, setLookupId] = useState("");
  const [decision, setDecision] = useState<ReviewDecision>("approved");
  const [reviewerRole, setReviewerRole] = useState("");
  const [comments, setComments] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  const createKey = useRef("");
  const reviewKey = useRef("");

  function invalidateCreateKey() {
    createKey.current = "";
  }

  function updateMetric(name: MetricName, value: string) {
    invalidateCreateKey();
    setMetrics((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function createReview() {
    if (objective.trim().length < 3) {
      setError("Provide a campaign objective of at least three characters.");
      return;
    }

    const metricPayload: Record<
      string,
      {
        value: string;
        provenance: "actual";
        evidence_id: string;
        source: string;
      }
    > = {};

    for (const definition of metricDefinitions) {
      const value = metrics[definition.key].trim();

      if (!value) continue;

      if (!Number.isFinite(Number(value)) || Number(value) < 0) {
        setError(`${definition.label} must be a non-negative number.`);
        return;
      }

      metricPayload[definition.key] = {
        value,
        provenance: "actual",
        evidence_id: `dashboard-${definition.key}`,
        source: "dashboard_manual_entry",
      };
    }

    if (!Object.keys(metricPayload).length) {
      setError("Provide at least one actual campaign metric.");
      return;
    }

    if (
      metrics.clicks &&
      metrics.impressions &&
      Number(metrics.clicks) > Number(metrics.impressions)
    ) {
      setError("Clicks cannot exceed impressions.");
      return;
    }

    if (
      metrics.conversions &&
      metrics.clicks &&
      Number(metrics.conversions) > Number(metrics.clicks)
    ) {
      setError("Conversions cannot exceed clicks.");
      return;
    }

    if (!createKey.current) {
      createKey.current = createIdempotencyKey("expert-run");
    }

    setBusy("create");
    setError("");

    try {
      const response = await fetch(`${API_URL}/v1/expert-reviews`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": createKey.current,
        },
        body: JSON.stringify({
          evidence: {
            objective: objective.trim(),
            mode: "shadow",
            currency: currency.trim().toUpperCase(),
            metrics: metricPayload,
            evidence: [],
            assumptions: assumptions
              .split("\n")
              .map((item) => item.trim())
              .filter(Boolean),
          },
        }),
      });

      const result = await readResponse<ExpertReviewRun>(response);
      setRun(result);
      setLookupId(result.run_id);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The analysis could not be created.",
      );
    } finally {
      setBusy("");
    }
  }

  async function loadRun(id = lookupId) {
    const normalizedId = id.trim();

    if (!normalizedId) {
      setError("Enter an expert-review run ID.");
      return;
    }

    setBusy("load");
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/v1/expert-reviews/${encodeURIComponent(normalizedId)}`,
        {
          credentials: "include",
          cache: "no-store",
        },
      );

      const result = await readResponse<ExpertReviewRun>(response);
      setRun(result);
      setLookupId(result.run_id);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The run could not be loaded.",
      );
    } finally {
      setBusy("");
    }
  }

  async function submitReview() {
    if (!run?.report_hash) {
      setError("This run has no verified report hash.");
      return;
    }

    if (reviewerRole.trim().length < 3) {
      setError("Provide the human reviewer's professional role.");
      return;
    }

    if (!reviewKey.current) {
      reviewKey.current = createIdempotencyKey("human-review");
    }

    setBusy("review");
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/v1/expert-reviews/${encodeURIComponent(run.run_id)}/review`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "Idempotency-Key": reviewKey.current,
          },
          body: JSON.stringify({
            decision,
            report_hash: run.report_hash,
            reviewer_role: reviewerRole.trim(),
            comments: comments.trim(),
          }),
        },
      );

      const result = await readResponse<ExpertReviewRun>(response);
      setRun(result);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The human-review decision could not be recorded.",
      );
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="mx-auto max-w-[1600px] space-y-7">
      <header className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-blue-600">
            Governed agent intelligence
          </p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">
            Expert Review
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            Run evidence-constrained campaign analysis through four governed
            specialists, deterministic validation, and an
            organization-authorized human review gate.
          </p>
        </div>

        <div className="flex items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-black text-emerald-700">
          <ShieldCheck size={19} />
          Shadow Mode enforced
        </div>
      </header>

      {error && (
        <section className="flex gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertTriangle className="mt-0.5 shrink-0" size={18} />
          <span>{error}</span>
        </section>
      )}

      <section className="grid gap-6 xl:grid-cols-[1fr_0.48fr]">
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <Brain className="text-blue-600" />
            <div>
              <h2 className="text-xl font-black">Evidence intake</h2>
              <p className="text-sm text-slate-500">
                Enter actual campaign evidence. Unsupported claims are rejected.
              </p>
            </div>
          </div>

          <label className="mt-6 block text-sm font-bold">
            Campaign objective
            <textarea
              value={objective}
              onChange={(event) => {
                invalidateCreateKey();
                setObjective(event.target.value);
              }}
              rows={4}
              placeholder="Generate qualified leads while maintaining the target CPA."
              className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-blue-500"
            />
          </label>

          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {metricDefinitions.map((metric) => (
              <label key={metric.key} className="text-sm font-bold">
                {metric.label}
                <input
                  type="number"
                  min="0"
                  step={metric.step}
                  value={metrics[metric.key]}
                  onChange={(event) =>
                    updateMetric(metric.key, event.target.value)
                  }
                  placeholder="Unknown"
                  className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-blue-500"
                />
              </label>
            ))}

            <label className="text-sm font-bold">
              Currency
              <input
                value={currency}
                maxLength={3}
                onChange={(event) => {
                  invalidateCreateKey();
                  setCurrency(event.target.value.toUpperCase());
                }}
                className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 font-normal uppercase outline-none focus:border-blue-500"
              />
            </label>
          </div>

          <label className="mt-5 block text-sm font-bold">
            Declared assumptions
            <textarea
              value={assumptions}
              onChange={(event) => {
                invalidateCreateKey();
                setAssumptions(event.target.value);
              }}
              rows={3}
              placeholder="One assumption per line"
              className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-blue-500"
            />
          </label>

          <button
            type="button"
            onClick={createReview}
            disabled={Boolean(busy)}
            className="mt-6 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#1468F3] px-6 py-4 text-sm font-black text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy === "create" ? (
              <>
                <LoaderCircle size={18} className="animate-spin" />
                Running governed analysis
              </>
            ) : (
              <>
                <Sparkles size={18} />
                Start expert review
              </>
            )}
          </button>
        </article>

        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <RefreshCw className="text-blue-600" />
            <div>
              <h2 className="font-black">Retrieve run</h2>
              <p className="text-sm text-slate-500">
                Load an organization-scoped review by ID.
              </p>
            </div>
          </div>

          <label className="mt-6 block text-sm font-bold">
            Run ID
            <input
              value={lookupId}
              onChange={(event) => setLookupId(event.target.value)}
              placeholder="UUID"
              className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 font-mono text-xs font-normal outline-none focus:border-blue-500"
            />
          </label>

          <button
            type="button"
            onClick={() => loadRun()}
            disabled={Boolean(busy)}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl border border-slate-200 px-4 py-3 text-sm font-black transition hover:border-blue-500 hover:text-blue-700 disabled:opacity-50"
          >
            {busy === "load" ? (
              <LoaderCircle size={17} className="animate-spin" />
            ) : (
              <RefreshCw size={17} />
            )}
            Load latest state
          </button>

          <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4">
            <p className="flex items-center gap-2 text-sm font-black text-amber-800">
              <ShieldCheck size={17} />
              Execution authority
            </p>
            <p className="mt-2 text-xs leading-5 text-amber-700">
              This workflow can analyze evidence and create recommendations. It
              cannot publish campaigns, change budgets, or spend money.
            </p>
          </div>
        </article>
      </section>

      {run && (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400">
                Status
              </p>
              <span
                className={`mt-4 inline-flex rounded-full border px-3 py-1 text-xs font-black ${statusClasses(run.status)}`}
              >
                {run.status.replaceAll("_", " ")}
              </span>
            </article>

            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400">
                Engine
              </p>
              <p className="mt-4 text-xl font-black capitalize">
                {run.analysis_engine}
              </p>
            </article>

            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400">
                Automated validation
              </p>
              <p className="mt-4 text-xl font-black">
                {run.validation?.passed ? "Passed" : "Not passed"}
              </p>
            </article>

            <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400">
                Human review
              </p>
              <p className="mt-4 text-sm font-black">{run.review_label}</p>
            </article>
          </section>

          {run.error_message && (
            <section className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">
              {run.error_message}
            </section>
          )}

          {run.validation && run.validation.issues.length > 0 && (
            <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="flex items-center gap-2 text-xl font-black">
                <ClipboardCheck className="text-blue-600" />
                Validation findings
              </h2>

              <div className="mt-5 space-y-3">
                {run.validation.issues.map((issue, index) => (
                  <div
                    key={`${issue.code}-${issue.path}-${index}`}
                    className={`rounded-2xl border p-4 ${
                      issue.level === "error"
                        ? "border-red-200 bg-red-50"
                        : "border-amber-200 bg-amber-50"
                    }`}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-black uppercase">
                        {issue.level}
                      </span>
                      <code className="text-xs">{issue.path}</code>
                    </div>
                    <p className="mt-2 text-sm">{issue.message}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {run.report && (
            <>
              <section className="rounded-3xl bg-slate-950 p-7 text-white shadow-xl">
                <div className="flex flex-col gap-6 xl:flex-row xl:justify-between">
                  <div className="max-w-4xl">
                    <p className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.18em] text-blue-300">
                      <BadgeCheck size={17} />
                      Evidence-constrained report
                    </p>
                    <h2 className="mt-4 text-2xl font-black">
                      Executive summary
                    </h2>
                    <p className="mt-4 leading-7 text-slate-200">
                      {run.report.executive_summary}
                    </p>
                  </div>

                  <div className="min-w-56 rounded-2xl border border-white/15 bg-white/10 p-5">
                    <p className="text-xs font-bold uppercase text-slate-300">
                      Data quality
                    </p>
                    <p className="mt-3 text-4xl font-black">
                      {percentage(run.report.data_quality_score)}
                    </p>
                    <p className="mt-2 text-xs text-slate-300">
                      Deterministic evidence score
                    </p>
                  </div>
                </div>

                <div className="mt-6 grid gap-3 sm:grid-cols-3">
                  <div className="rounded-2xl bg-white/10 p-4">
                    <p className="text-xs text-slate-300">Shadow Mode</p>
                    <p className="mt-1 font-black text-emerald-300">Enforced</p>
                  </div>
                  <div className="rounded-2xl bg-white/10 p-4">
                    <p className="text-xs text-slate-300">
                      Automated validation
                    </p>
                    <p className="mt-1 font-black text-emerald-300">
                      {run.report.automated_validation_passed
                        ? "Passed"
                        : "Failed"}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-white/10 p-4">
                    <p className="text-xs text-slate-300">Live execution</p>
                    <p className="mt-1 font-black text-amber-300">Disabled</p>
                  </div>
                </div>
              </section>

              <section>
                <div className="flex items-center gap-3">
                  <Brain className="text-blue-600" />
                  <h2 className="text-2xl font-black">
                    Specialist assessments
                  </h2>
                </div>

                <div className="mt-5 grid gap-5 xl:grid-cols-2">
                  {run.report.specialist_assessments.map((assessment) => (
                    <article
                      key={assessment.agent_id}
                      className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
                    >
                      <div>
                        <p className="text-xs font-black uppercase tracking-wide text-blue-600">
                          {assessment.agent_id.replaceAll("_", " ")}
                        </p>
                        <h3 className="mt-1 text-xl font-black">
                          {assessment.role_name}
                        </h3>
                      </div>

                      <div className="mt-5 space-y-4">
                        {assessment.findings.map((finding, index) => (
                          <div
                            key={`${finding.title}-${index}`}
                            className="rounded-2xl border border-slate-200 p-4"
                          >
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <h4 className="font-black">{finding.title}</h4>
                              <span
                                className={`rounded-full border px-2.5 py-1 text-[10px] font-black uppercase ${severityClasses(finding.severity)}`}
                              >
                                {finding.severity}
                              </span>
                            </div>
                            <p className="mt-3 text-sm leading-6 text-slate-600">
                              {finding.observation}
                            </p>
                            <p className="mt-3 text-xs font-bold text-slate-500">
                              Confidence: {percentage(finding.confidence)}
                            </p>
                            {finding.evidence_ids.length > 0 && (
                              <div className="mt-3 flex flex-wrap gap-2">
                                {finding.evidence_ids.map((evidenceId) => (
                                  <code
                                    key={evidenceId}
                                    className="rounded-lg bg-blue-50 px-2 py-1 text-[10px] text-blue-700"
                                  >
                                    {evidenceId}
                                  </code>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>

                      {assessment.missing_information.length > 0 && (
                        <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4">
                          <p className="text-xs font-black uppercase text-amber-700">
                            Missing information
                          </p>
                          <ul className="mt-2 space-y-1 text-sm text-amber-800">
                            {assessment.missing_information.map((item) => (
                              <li key={item}>• {item}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </article>
                  ))}
                </div>
              </section>

              <section>
                <div className="flex items-center gap-3">
                  <Sparkles className="text-blue-600" />
                  <h2 className="text-2xl font-black">
                    Prioritized recommendations
                  </h2>
                </div>

                <div className="mt-5 grid gap-5 xl:grid-cols-2">
                  {run.report.prioritized_recommendations.map(
                    (recommendation, index) => (
                      <article
                        key={`${recommendation.title}-${index}`}
                        className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <h3 className="text-lg font-black">
                            {recommendation.title}
                          </h3>
                          <span
                            className={`rounded-full border px-3 py-1 text-xs font-black ${severityClasses(recommendation.risk)}`}
                          >
                            {percentage(recommendation.confidence)} confidence
                          </span>
                        </div>

                        <p className="mt-4 text-sm leading-6 text-slate-600">
                          {recommendation.rationale}
                        </p>

                        <dl className="mt-5 grid gap-3">
                          <div className="rounded-2xl bg-emerald-50 p-4">
                            <dt className="text-xs font-black uppercase text-emerald-700">
                              Expected impact
                            </dt>
                            <dd className="mt-1 text-sm text-emerald-950">
                              {recommendation.expected_impact}
                            </dd>
                          </div>
                          <div className="rounded-2xl bg-slate-50 p-4">
                            <dt className="text-xs font-black uppercase text-slate-500">
                              Measurement plan
                            </dt>
                            <dd className="mt-1 text-sm text-slate-800">
                              {recommendation.measurement_plan}
                            </dd>
                          </div>
                        </dl>

                        <div className="mt-4 flex flex-wrap gap-2">
                          {recommendation.evidence_ids.map((evidenceId) => (
                            <code
                              key={evidenceId}
                              className="rounded-lg bg-blue-50 px-2 py-1 text-[10px] text-blue-700"
                            >
                              {evidenceId}
                            </code>
                          ))}
                        </div>
                      </article>
                    ),
                  )}
                </div>
              </section>

              <section className="grid gap-6 xl:grid-cols-[0.7fr_1.3fr]">
                <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex items-center gap-3">
                    <FileKey2 className="text-blue-600" />
                    <h2 className="text-xl font-black">Report integrity</h2>
                  </div>

                  <dl className="mt-5 space-y-4 text-sm">
                    <div>
                      <dt className="font-bold text-slate-500">Run ID</dt>
                      <dd className="mt-1 break-all font-mono text-xs">
                        {run.run_id}
                      </dd>
                    </div>
                    <div>
                      <dt className="font-bold text-slate-500">Report hash</dt>
                      <dd className="mt-1 break-all font-mono text-xs">
                        {run.report_hash}
                      </dd>
                    </div>
                    <div>
                      <dt className="font-bold text-slate-500">Rubric</dt>
                      <dd className="mt-1">{run.rubric_version}</dd>
                    </div>
                    <div>
                      <dt className="font-bold text-slate-500">Completed</dt>
                      <dd className="mt-1">{formatDate(run.completed_at)}</dd>
                    </div>
                  </dl>
                </article>

                <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex items-center gap-3">
                    <ClipboardCheck className="text-blue-600" />
                    <div>
                      <h2 className="text-xl font-black">Human review gate</h2>
                      <p className="text-sm text-slate-500">
                        Approval is recorded against the immutable report hash.
                      </p>
                    </div>
                  </div>

                  {run.human_review ? (
                    <div
                      className={`mt-6 rounded-2xl border p-5 ${
                        run.human_review.decision === "approved"
                          ? "border-emerald-200 bg-emerald-50"
                          : "border-amber-200 bg-amber-50"
                      }`}
                    >
                      <p className="flex items-center gap-2 font-black">
                        {run.human_review.decision === "approved" ? (
                          <CheckCircle2
                            size={19}
                            className="text-emerald-600"
                          />
                        ) : (
                          <XCircle size={19} className="text-amber-700" />
                        )}
                        {run.review_label}
                      </p>
                      <p className="mt-3 text-sm">
                        Reviewer role: {run.human_review.reviewer_role}
                      </p>
                      <p className="mt-1 text-sm">
                        Reviewed: {formatDate(run.human_review.reviewed_at)}
                      </p>
                      {run.human_review.comments && (
                        <p className="mt-3 text-sm leading-6">
                          {run.human_review.comments}
                        </p>
                      )}
                    </div>
                  ) : run.review_required ? (
                    <>
                      <div className="mt-6 grid gap-4 sm:grid-cols-2">
                        <label className="text-sm font-bold">
                          Decision
                          <select
                            value={decision}
                            onChange={(event) => {
                              reviewKey.current = "";
                              setDecision(event.target.value as ReviewDecision);
                            }}
                            className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 font-normal"
                          >
                            <option value="approved">Approve</option>
                            <option value="revision_required">
                              Require revision
                            </option>
                            <option value="rejected">Reject</option>
                          </select>
                        </label>

                        <label className="text-sm font-bold">
                          Professional role
                          <input
                            value={reviewerRole}
                            onChange={(event) => {
                              reviewKey.current = "";
                              setReviewerRole(event.target.value);
                            }}
                            placeholder="Senior Paid Media Strategist"
                            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-blue-500"
                          />
                        </label>
                      </div>

                      <label className="mt-4 block text-sm font-bold">
                        Review comments
                        <textarea
                          value={comments}
                          onChange={(event) => {
                            reviewKey.current = "";
                            setComments(event.target.value);
                          }}
                          rows={4}
                          placeholder="Document the evidence checked, limitations, and required revisions."
                          className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-blue-500"
                        />
                      </label>

                      <button
                        type="button"
                        onClick={submitReview}
                        disabled={Boolean(busy)}
                        className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#1468F3] px-6 py-4 text-sm font-black text-white transition hover:bg-blue-700 disabled:opacity-50"
                      >
                        {busy === "review" ? (
                          <LoaderCircle size={18} className="animate-spin" />
                        ) : (
                          <BadgeCheck size={18} />
                        )}
                        Record verified decision
                      </button>
                    </>
                  ) : (
                    <div className="mt-6 rounded-2xl bg-slate-50 p-5 text-sm text-slate-600">
                      Human review becomes available only after automated
                      validation passes.
                    </div>
                  )}
                </article>
              </section>
            </>
          )}
        </>
      )}
    </main>
  );
}
