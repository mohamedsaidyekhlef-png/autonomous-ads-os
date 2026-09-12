"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  Brain,
  CheckCircle2,
  Download,
  FileArchive,
  FileSpreadsheet,
  ImageDown,
  Link2,
  LoaderCircle,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
} from "lucide-react";
import JSZip from "jszip";
import Papa from "papaparse";
import { toPng } from "html-to-image";

const API_URL =
  process.env.NODE_ENV === "production"
    ? "/api"
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080");

type CampaignRow = {
  date: string;
  campaign: string;
  adGroup: string;
  impressions: number;
  clicks: number;
  spend: number;
  conversions: number;
  revenue: number;
};

type Recommendation = {
  title: string;
  rationale: string;
  expected_impact: string;
  risk: string;
  confidence: number;
  measurement: string;
};

type AnalysisRun = {
  run_id: string;
  status: string;
  model?: string;
  elapsed_seconds?: number;
  warnings?: string[];
  result?: {
    executive_summary: string;
    diagnosis: string[];
    assumptions?: string[];
    missing_information?: string[];
    recommendations: Recommendation[];
  };
};

type MetricCardProps = {
  label: string;
  value: string;
  source: "Actual" | "Calculated" | "AI estimate" | "Unknown";
  note: string;
};

type CsvCell = string | number;
type CsvRow = Record<string, CsvCell>;
type ReportTables = Record<string, CsvRow[]>;

const aliases: Record<keyof CampaignRow, string[]> = {
  date: ["date", "day"],
  campaign: ["campaign", "campaign_name", "campaignname"],
  adGroup: ["ad_group", "adgroup", "ad_group_name", "adgroupname"],
  impressions: ["impressions", "impr"],
  clicks: ["clicks"],
  spend: ["spend", "cost", "amount_spent"],
  conversions: ["conversions", "conv", "results"],
  revenue: ["revenue", "conversion_value", "conversionvalue", "sales"],
};

function normalizeHeader(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_");
}

function field(record: Record<string, string>, names: string[], fallback = "") {
  const normalized = Object.fromEntries(
    Object.entries(record).map(([key, value]) => [
      normalizeHeader(key),
      String(value ?? "").trim(),
    ]),
  );

  for (const name of names) {
    const value = normalized[normalizeHeader(name)];
    if (value !== undefined && value !== "") return value;
  }

  return fallback;
}

function numeric(value: string) {
  const parsed = Number(value.replace(/[$,%\s,]/g, ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

function money(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function compact(value: number) {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function percent(value: number) {
  return `${value.toFixed(2)}%`;
}

function safeCsvValue(value: unknown) {
  const text = String(value ?? "");
  return /^[=+\-@]/.test(text) ? `'${text}` : text;
}

function MetricCard({ label, value, source, note }: MetricCardProps) {
  const colors = {
    Actual: "bg-emerald-50 text-emerald-700 border-emerald-200",
    Calculated: "bg-blue-50 text-blue-700 border-blue-200",
    "AI estimate": "bg-violet-50 text-violet-700 border-violet-200",
    Unknown: "bg-slate-50 text-slate-600 border-slate-200",
  };

  return (
    <article
      data-export-card
      className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-semibold text-slate-500">{label}</p>
        <span
          className={`rounded-full border px-2 py-1 text-[10px] font-black uppercase tracking-wide ${colors[source]}`}
        >
          {source}
        </span>
      </div>
      <p className="mt-4 text-3xl font-black tracking-tight text-slate-950">
        {value}
      </p>
      <p className="mt-2 text-xs leading-5 text-slate-500">{note}</p>
    </article>
  );
}

export function CampaignAnalysis() {
  const [campaignUrl, setCampaignUrl] = useState("");
  const [landingPage, setLandingPage] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [campaignId, setCampaignId] = useState("");
  const [objective, setObjective] = useState("");
  const [budget, setBudget] = useState("");
  const [notes, setNotes] = useState("");
  const [rows, setRows] = useState<CampaignRow[]>([]);
  const [fileName, setFileName] = useState("");
  const [analysis, setAnalysis] = useState<AnalysisRun | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState("");

  const totals = useMemo(() => {
    const total = rows.reduce(
      (result, row) => ({
        impressions: result.impressions + row.impressions,
        clicks: result.clicks + row.clicks,
        spend: result.spend + row.spend,
        conversions: result.conversions + row.conversions,
        revenue: result.revenue + row.revenue,
      }),
      {
        impressions: 0,
        clicks: 0,
        spend: 0,
        conversions: 0,
        revenue: 0,
      },
    );

    return {
      ...total,
      ctr: total.impressions ? (total.clicks / total.impressions) * 100 : 0,
      cpc: total.clicks ? total.spend / total.clicks : 0,
      cvr: total.clicks ? (total.conversions / total.clicks) * 100 : 0,
      cpa: total.conversions ? total.spend / total.conversions : 0,
      roas: total.spend ? total.revenue / total.spend : 0,
    };
  }, [rows]);

  const campaignBreakdown = useMemo(() => {
    const values = new Map<string, { spend: number; conversions: number }>();

    for (const row of rows) {
      const key = row.campaign || "Unspecified campaign";
      const current = values.get(key) ?? { spend: 0, conversions: 0 };
      current.spend += row.spend;
      current.conversions += row.conversions;
      values.set(key, current);
    }

    return [...values.entries()]
      .map(([name, value]) => ({ name, ...value }))
      .sort((a, b) => b.spend - a.spend)
      .slice(0, 8);
  }, [rows]);

  const dailyTrend = useMemo(() => {
    const values = new Map<string, number>();

    for (const row of rows) {
      const key = row.date || "Unknown";
      values.set(key, (values.get(key) ?? 0) + row.spend);
    }

    return [...values.entries()]
      .map(([date, spend]) => ({ date, spend }))
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(-14);
  }, [rows]);

  const recommendations = analysis?.result?.recommendations ?? [];
  const averageConfidence = recommendations.length
    ? recommendations.reduce((sum, item) => sum + item.confidence, 0) /
      recommendations.length
    : 0;

  const riskCounts = recommendations.reduce(
    (result, item) => {
      const risk = item.risk.toLowerCase();
      if (risk.includes("high")) result.high += 1;
      else if (risk.includes("low")) result.low += 1;
      else result.medium += 1;
      return result;
    },
    { low: 0, medium: 0, high: 0 },
  );

  function uploadCsv(file: File) {
    setError("");
    setFileName(file.name);

    Papa.parse<Record<string, string>>(file, {
      header: true,
      skipEmptyLines: true,
      complete(result) {
        const parsed = result.data.map((record, index) => ({
          date: field(record, aliases.date, `Row ${index + 1}`),
          campaign: field(record, aliases.campaign, "Imported campaign"),
          adGroup: field(record, aliases.adGroup, "Unspecified"),
          impressions: numeric(field(record, aliases.impressions)),
          clicks: numeric(field(record, aliases.clicks)),
          spend: numeric(field(record, aliases.spend)),
          conversions: numeric(field(record, aliases.conversions)),
          revenue: numeric(field(record, aliases.revenue)),
        }));

        if (!parsed.length) {
          setError("The CSV did not contain any campaign records.");
          setRows([]);
          return;
        }

        setRows(parsed);
      },
      error(parseError) {
        setError(`CSV import failed: ${parseError.message}`);
        setRows([]);
      },
    });
  }

  async function analyze() {
    if (!objective.trim() && !campaignUrl.trim() && !rows.length) {
      setError(
        "Provide an objective, campaign URL, or campaign-performance CSV.",
      );
      return;
    }

    setBusy(true);
    setError("");
    setAnalysis(null);

    const prompt = [
      "Perform an expert-framework advertising campaign analysis.",
      `Campaign URL supplied: ${campaignUrl || "No"}`,
      `Landing page: ${landingPage || "Not supplied"}`,
      `Google Ads customer ID: ${customerId || "Not supplied"}`,
      `Campaign ID: ${campaignId || "Not supplied"}`,
      `Objective: ${objective || "Not supplied"}`,
      `Monthly budget: ${budget || "Not supplied"}`,
      `Analyst notes: ${notes || "None"}`,
      `Uploaded rows: ${rows.length}`,
      `Actual impressions: ${totals.impressions}`,
      `Actual clicks: ${totals.clicks}`,
      `Actual spend: ${totals.spend}`,
      `Actual conversions: ${totals.conversions}`,
      `Actual conversion value: ${totals.revenue}`,
      `Calculated CTR: ${totals.ctr}`,
      `Calculated CPC: ${totals.cpc}`,
      `Calculated CVR: ${totals.cvr}`,
      `Calculated CPA: ${totals.cpa}`,
      `Calculated ROAS: ${totals.roas}`,
      "",
      "Identify what is working, what is not working, missing information,",
      "tracking risks, wasted-spend risks, budget issues, targeting issues,",
      "creative and landing-page issues, and prioritized recommendations.",
      "Do not claim the supplied URL was crawled.",
      "Do not invent account metrics.",
      "Treat zero metrics as unknown when no CSV rows were uploaded.",
      "Do not perform live advertising actions.",
    ].join("\n");

    try {
      const response = await fetch(`${API_URL}/v1/command/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: prompt, mode: "shadow" }),
      });

      const contentType = response.headers.get("content-type") ?? "";
      const payload = contentType.includes("application/json")
        ? ((await response.json()) as AnalysisRun & { detail?: string })
        : { detail: "The analysis endpoint returned an invalid response." };

      if (!response.ok) {
        throw new Error(
          "detail" in payload && payload.detail
            ? payload.detail
            : "Campaign analysis failed.",
        );
      }

      setAnalysis(payload as AnalysisRun);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Campaign analysis could not be completed.",
      );
    } finally {
      setBusy(false);
    }
  }

  function reportTables(): ReportTables {
    const campaignData: CsvRow[] = rows.map((row) => ({
      Date: safeCsvValue(row.date),
      Campaign: safeCsvValue(row.campaign),
      "Ad group": safeCsvValue(row.adGroup),
      Impressions: row.impressions,
      Clicks: row.clicks,
      Spend: row.spend,
      Conversions: row.conversions,
      Revenue: row.revenue,
    }));

    const calculatedKpis: CsvRow[] = [
      {
        Impressions: totals.impressions,
        Clicks: totals.clicks,
        Spend: totals.spend,
        Conversions: totals.conversions,
        Revenue: totals.revenue,
        "CTR percent": totals.ctr,
        CPC: totals.cpc,
        "CVR percent": totals.cvr,
        CPA: totals.cpa,
        ROAS: totals.roas,
      },
    ];

    const recommendationData: CsvRow[] = recommendations.map((item) => ({
      Title: safeCsvValue(item.title),
      Rationale: safeCsvValue(item.rationale),
      "Expected impact": safeCsvValue(item.expected_impact),
      Risk: safeCsvValue(item.risk),
      "AI confidence percent": Math.round(item.confidence * 100),
      Measurement: safeCsvValue(item.measurement),
    }));

    const diagnosisData: CsvRow[] = (analysis?.result?.diagnosis ?? []).map(
      (item) => ({
        Diagnosis: safeCsvValue(item),
      }),
    );

    return {
      "campaign-data.csv": campaignData,
      "calculated-kpis.csv": calculatedKpis,
      "recommendations.csv": recommendationData,
      "diagnosis.csv": diagnosisData,
    };
  }
  async function downloadCsvZip(excelCompatible: boolean) {
    setExporting(excelCompatible ? "excel" : "csv");
    setError("");

    try {
      const zip = new JSZip();
      const prefix = excelCompatible ? "\uFEFF" : "";
      const tables = reportTables();

      for (const [name, rowsToExport] of Object.entries(tables)) {
        const csv = Papa.unparse<CsvRow>(rowsToExport, {
          header: true,
          newline: "\r\n",
          skipEmptyLines: true,
        });

        zip.file(name, `${prefix}${csv}`);
      }

      zip.file(
        "README.txt",
        [
          "Autonomous Ads OS campaign analysis",
          "",
          "DATA PROVENANCE",
          "ACTUAL values originate from the uploaded CSV.",
          "CALCULATED values are derived from uploaded metrics.",
          "AI confidence values are estimates, not measured performance.",
          "",
          "REVIEW STATUS",
          "AI analysis: completed",
          "Expert framework: applied",
          "Human expert review: required",
          "",
          "SAFETY",
          "No live campaign action was performed.",
          "Shadow Mode remained enabled during analysis.",
        ].join("\r\n"),
      );

      const blob = await zip.generateAsync({
        type: "blob",
        compression: "DEFLATE",
        compressionOptions: {
          level: 6,
        },
      });

      saveBlob(
        blob,
        excelCompatible
          ? "campaign-analysis-excel.zip"
          : "campaign-analysis-csv.zip",
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? `Report export failed: ${caught.message}`
          : "Report export could not be completed.",
      );
    } finally {
      setExporting("");
    }
  }
  async function downloadPngZip() {
    setExporting("png");

    try {
      const zip = new JSZip();
      const cards =
        document.querySelectorAll<HTMLElement>("[data-export-card]");

      for (let index = 0; index < cards.length; index += 1) {
        const dataUrl = await toPng(cards[index], {
          backgroundColor: "#ffffff",
          pixelRatio: 2,
          cacheBust: true,
        });

        zip.file(
          `report-card-${String(index + 1).padStart(2, "0")}.png`,
          dataUrl.split(",")[1],
          { base64: true },
        );
      }

      const blob = await zip.generateAsync({ type: "blob" });
      saveBlob(blob, "campaign-analysis-cards.zip");
    } finally {
      setExporting("");
    }
  }

  function saveBlob(blob: Blob, name: string) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = name;
    link.click();
    URL.revokeObjectURL(url);
  }

  const maximumCampaignSpend = Math.max(
    1,
    ...campaignBreakdown.map((item) => item.spend),
  );

  const maximumDailySpend = Math.max(
    1,
    ...dailyTrend.map((item) => item.spend),
  );

  return (
    <main className="mx-auto max-w-[1600px] space-y-8">
      <header className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-blue-600">
            Performance intelligence
          </p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">
            Campaign Analysis
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            Analyze imported campaign performance and produce an auditable
            Shadow Mode report. Uploaded metrics are calculated locally before
            summarized context is sent to the AI.
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs font-black text-emerald-700">
          <ShieldCheck size={18} />
          No campaign mutations or spending
        </div>
      </header>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <Search className="text-blue-600" />
            <div>
              <h2 className="text-xl font-black">Analysis intake</h2>
              <p className="text-sm text-slate-500">
                URLs are recorded as context and are not automatically crawled.
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <label className="space-y-2 text-sm font-bold">
              Campaign URL
              <div className="flex items-center gap-2 rounded-2xl border border-slate-200 px-4">
                <Link2 size={17} className="text-slate-400" />
                <input
                  value={campaignUrl}
                  onChange={(event) => setCampaignUrl(event.target.value)}
                  placeholder="https://ads.google.com/..."
                  className="min-w-0 flex-1 py-3 outline-none"
                />
              </div>
            </label>

            <label className="space-y-2 text-sm font-bold">
              Landing-page URL
              <input
                value={landingPage}
                onChange={(event) => setLandingPage(event.target.value)}
                placeholder="https://example.com/landing-page"
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-blue-500"
              />
            </label>

            <label className="space-y-2 text-sm font-bold">
              Google Ads customer ID
              <input
                value={customerId}
                onChange={(event) => setCustomerId(event.target.value)}
                placeholder="123-456-7890"
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-blue-500"
              />
            </label>

            <label className="space-y-2 text-sm font-bold">
              Campaign ID
              <input
                value={campaignId}
                onChange={(event) => setCampaignId(event.target.value)}
                placeholder="Campaign ID or external reference"
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-blue-500"
              />
            </label>

            <label className="space-y-2 text-sm font-bold md:col-span-2">
              Campaign objective
              <textarea
                value={objective}
                onChange={(event) => setObjective(event.target.value)}
                placeholder="Describe the offer, audience, geography, objective and current concerns."
                rows={4}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-blue-500"
              />
            </label>

            <label className="space-y-2 text-sm font-bold">
              Monthly budget
              <input
                value={budget}
                onChange={(event) => setBudget(event.target.value)}
                placeholder="$3,000"
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-blue-500"
              />
            </label>

            <label className="space-y-2 text-sm font-bold">
              Analyst notes
              <input
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Known tracking or targeting concerns"
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-blue-500"
              />
            </label>
          </div>

          <button
            onClick={analyze}
            disabled={busy}
            className="mt-6 flex w-full items-center justify-center gap-2 rounded-2xl bg-blue-600 px-6 py-4 text-sm font-black text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {busy ? (
              <>
                <LoaderCircle className="animate-spin" size={18} />
                Analyzing…
              </>
            ) : (
              <>
                <Sparkles size={18} />
                Analyze campaign
              </>
            )}
          </button>

          {error && (
            <div className="mt-4 flex gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <AlertTriangle className="shrink-0" size={18} />
              {error}
            </div>
          )}
        </article>

        <article className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-6">
          <div className="flex items-center gap-3">
            <Upload className="text-blue-600" />
            <div>
              <h2 className="text-xl font-black">Performance data</h2>
              <p className="text-sm text-slate-500">
                Upload a Google Ads or normalized CSV export.
              </p>
            </div>
          </div>

          <label className="mt-6 flex cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed border-blue-200 bg-white px-6 py-12 text-center transition hover:border-blue-500">
            <FileSpreadsheet size={38} className="text-blue-600" />
            <span className="mt-4 font-black">
              {fileName || "Choose campaign CSV"}
            </span>
            <span className="mt-2 text-xs text-slate-500">
              Supported fields: date, campaign, ad group, impressions, clicks,
              spend, conversions and revenue.
            </span>
            <input
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) uploadCsv(file);
              }}
            />
          </label>

          <div className="mt-5 grid grid-cols-2 gap-3">
            <div className="rounded-2xl bg-white p-4">
              <p className="text-xs font-bold uppercase text-slate-400">Rows</p>
              <p className="mt-2 text-2xl font-black">{rows.length}</p>
            </div>
            <div className="rounded-2xl bg-white p-4">
              <p className="text-xs font-bold uppercase text-slate-400">
                Data status
              </p>
              <p className="mt-2 font-black">
                {rows.length ? "Imported" : "Not supplied"}
              </p>
            </div>
          </div>

          <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs leading-5 text-amber-800">
            A campaign URL or ID does not grant access to private Google Ads
            performance. Connect Google OAuth read-only or upload an export for
            actual metrics.
          </div>
        </article>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard
          label="Spend"
          value={rows.length ? money(totals.spend) : "Unknown"}
          source={rows.length ? "Actual" : "Unknown"}
          note="Imported advertising cost."
        />
        <MetricCard
          label="CTR"
          value={rows.length ? percent(totals.ctr) : "Unknown"}
          source={rows.length ? "Calculated" : "Unknown"}
          note="Clicks divided by impressions."
        />
        <MetricCard
          label="CPC"
          value={rows.length ? money(totals.cpc) : "Unknown"}
          source={rows.length ? "Calculated" : "Unknown"}
          note="Spend divided by clicks."
        />
        <MetricCard
          label="CPA"
          value={
            rows.length && totals.conversions ? money(totals.cpa) : "Unknown"
          }
          source={rows.length && totals.conversions ? "Calculated" : "Unknown"}
          note="Spend divided by conversions."
        />
        <MetricCard
          label="ROAS"
          value={
            rows.length && totals.revenue
              ? `${totals.roas.toFixed(2)}×`
              : "Unknown"
          }
          source={rows.length && totals.revenue ? "Calculated" : "Unknown"}
          note="Conversion value divided by spend."
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <article
          data-export-card
          className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <div className="flex items-center gap-3">
            <BarChart3 className="text-blue-600" />
            <div>
              <h2 className="font-black">Campaign spend distribution</h2>
              <p className="text-xs text-slate-500">
                Actual imported spend by campaign
              </p>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            {campaignBreakdown.length ? (
              campaignBreakdown.map((item) => (
                <div key={item.name}>
                  <div className="flex justify-between gap-3 text-sm">
                    <span className="truncate font-bold">{item.name}</span>
                    <span className="font-black">{money(item.spend)}</span>
                  </div>
                  <div className="mt-2 h-3 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-blue-600 to-cyan-400"
                      style={{
                        width: `${Math.max(
                          3,
                          (item.spend / maximumCampaignSpend) * 100,
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <p className="rounded-2xl bg-slate-50 p-8 text-center text-sm text-slate-500">
                Upload campaign data to generate this chart.
              </p>
            )}
          </div>
        </article>

        <article
          data-export-card
          className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <div className="flex items-center gap-3">
            <BarChart3 className="text-violet-600" />
            <div>
              <h2 className="font-black">Daily spend trend</h2>
              <p className="text-xs text-slate-500">
                Last 14 imported reporting dates
              </p>
            </div>
          </div>

          <div className="mt-6 flex h-56 items-end gap-2 rounded-2xl bg-slate-50 p-4">
            {dailyTrend.length ? (
              dailyTrend.map((item) => (
                <div
                  key={item.date}
                  className="group flex min-w-0 flex-1 flex-col items-center justify-end"
                  title={`${item.date}: ${money(item.spend)}`}
                >
                  <span className="mb-2 hidden text-[10px] font-bold group-hover:block">
                    {money(item.spend)}
                  </span>
                  <div
                    className="w-full rounded-t-lg bg-gradient-to-t from-violet-700 to-fuchsia-400"
                    style={{
                      height: `${Math.max(
                        6,
                        (item.spend / maximumDailySpend) * 160,
                      )}px`,
                    }}
                  />
                  <span className="mt-2 max-w-full truncate text-[9px] text-slate-400">
                    {item.date}
                  </span>
                </div>
              ))
            ) : (
              <div className="m-auto text-sm text-slate-500">
                Upload dated campaign data to generate the trend graph.
              </div>
            )}
          </div>
        </article>
      </section>

      {analysis?.result && (
        <>
          <section
            data-export-card
            className="rounded-3xl bg-gradient-to-br from-slate-950 via-blue-950 to-violet-950 p-7 text-white shadow-xl"
          >
            <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
              <div className="max-w-4xl">
                <div className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.18em] text-cyan-300">
                  <Brain size={17} />
                  Expert-framework analysis
                </div>
                <h2 className="mt-4 text-2xl font-black">Executive summary</h2>
                <p className="mt-4 leading-7 text-slate-200">
                  {analysis.result.executive_summary}
                </p>
              </div>

              <div className="min-w-52 rounded-3xl border border-white/15 bg-white/10 p-5">
                <p className="text-xs font-bold uppercase text-slate-300">
                  AI confidence estimate
                </p>
                <p className="mt-3 text-4xl font-black">
                  {Math.round(averageConfidence * 100)}%
                </p>
                <p className="mt-2 text-xs text-slate-300">
                  Not measured campaign performance
                </p>
              </div>
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl bg-white/10 p-4">
                <p className="text-xs text-slate-300">AI analysis</p>
                <p className="mt-1 font-black text-emerald-300">Completed</p>
              </div>
              <div className="rounded-2xl bg-white/10 p-4">
                <p className="text-xs text-slate-300">Expert framework</p>
                <p className="mt-1 font-black text-emerald-300">Applied</p>
              </div>
              <div className="rounded-2xl bg-white/10 p-4">
                <p className="text-xs text-slate-300">Human expert review</p>
                <p className="mt-1 font-black text-amber-300">Required</p>
              </div>
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-[1fr_0.45fr]">
            <article
              data-export-card
              className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <h2 className="text-xl font-black">Diagnosis</h2>
              <div className="mt-5 space-y-3">
                {analysis.result.diagnosis.map((item, index) => (
                  <div
                    key={`${item}-${index}`}
                    className="flex gap-3 rounded-2xl bg-slate-50 p-4 text-sm leading-6"
                  >
                    <CheckCircle2
                      size={18}
                      className="mt-1 shrink-0 text-blue-600"
                    />
                    {item}
                  </div>
                ))}
              </div>
            </article>

            <article
              data-export-card
              className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <h2 className="text-xl font-black">Risk distribution</h2>
              <div className="mt-6 space-y-5">
                {[
                  ["Low", riskCounts.low, "bg-emerald-500"],
                  ["Medium", riskCounts.medium, "bg-amber-500"],
                  ["High", riskCounts.high, "bg-red-500"],
                ].map(([label, count, color]) => (
                  <div key={String(label)}>
                    <div className="flex justify-between text-sm font-bold">
                      <span>{label}</span>
                      <span>{count}</span>
                    </div>
                    <div className="mt-2 h-3 rounded-full bg-slate-100">
                      <div
                        className={`h-full rounded-full ${color}`}
                        style={{
                          width: recommendations.length
                            ? `${(Number(count) / recommendations.length) * 100}%`
                            : "0%",
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </section>

          <section>
            <div className="flex items-center gap-3">
              <Sparkles className="text-blue-600" />
              <h2 className="text-2xl font-black">
                Prioritized recommendations
              </h2>
            </div>

            <div className="mt-5 grid gap-5 lg:grid-cols-2">
              {recommendations.map((item, index) => (
                <article
                  data-export-card
                  key={`${item.title}-${index}`}
                  className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-4">
                    <h3 className="text-lg font-black">{item.title}</h3>
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-black text-blue-700">
                      {Math.round(item.confidence * 100)}% AI estimate
                    </span>
                  </div>

                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-blue-600"
                      style={{ width: `${item.confidence * 100}%` }}
                    />
                  </div>

                  <p className="mt-5 text-sm leading-6 text-slate-600">
                    {item.rationale}
                  </p>

                  <dl className="mt-5 grid gap-3 text-sm">
                    <div className="rounded-2xl bg-emerald-50 p-4">
                      <dt className="text-xs font-black uppercase text-emerald-700">
                        Expected impact
                      </dt>
                      <dd className="mt-1 text-emerald-950">
                        {item.expected_impact}
                      </dd>
                    </div>
                    <div className="rounded-2xl bg-slate-50 p-4">
                      <dt className="text-xs font-black uppercase text-slate-500">
                        Measurement
                      </dt>
                      <dd className="mt-1 text-slate-800">
                        {item.measurement}
                      </dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <Download className="text-blue-600" />
              <div>
                <h2 className="text-xl font-black">Download report</h2>
                <p className="text-sm text-slate-500">
                  Export sanitized report data and presentation-ready cards.
                </p>
              </div>
            </div>

            <div className="mt-6 grid gap-3 md:grid-cols-3">
              <button
                onClick={() => downloadCsvZip(false)}
                disabled={Boolean(exporting)}
                className="flex items-center justify-center gap-2 rounded-2xl border border-slate-200 px-4 py-4 text-sm font-black hover:border-blue-500 hover:text-blue-700 disabled:opacity-50"
              >
                <FileArchive size={18} />
                {exporting === "csv" ? "Preparing…" : "CSV data (.zip)"}
              </button>

              <button
                onClick={() => downloadCsvZip(true)}
                disabled={Boolean(exporting)}
                className="flex items-center justify-center gap-2 rounded-2xl border border-slate-200 px-4 py-4 text-sm font-black hover:border-blue-500 hover:text-blue-700 disabled:opacity-50"
              >
                <FileSpreadsheet size={18} />
                {exporting === "excel" ? "Preparing…" : "CSV for Excel (.zip)"}
              </button>

              <button
                onClick={downloadPngZip}
                disabled={Boolean(exporting)}
                className="flex items-center justify-center gap-2 rounded-2xl border border-slate-200 px-4 py-4 text-sm font-black hover:border-blue-500 hover:text-blue-700 disabled:opacity-50"
              >
                <ImageDown size={18} />
                {exporting === "png" ? "Rendering…" : "Cards as PNG (.zip)"}
              </button>
            </div>
          </section>
        </>
      )}
    </main>
  );
}
