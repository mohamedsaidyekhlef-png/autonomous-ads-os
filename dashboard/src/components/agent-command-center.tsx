"use client";

import { useState } from "react";
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  LoaderCircle,
  Send,
  Sparkles,
} from "lucide-react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";

type Recommendation = {
  title: string;
  action_type: string;
  rationale: string;
  expected_impact: string;
  risk: "low" | "medium" | "high";
  confidence: number;
  measurement: string;
};

type CommandResponse = {
  run_id: string;
  status: string;
  mode: string;
  result: {
    executive_summary: string;
    interpretation: string;
    verified_observations: string[];
    assumptions: string[];
    missing_information: string[];
    diagnosis: string[];
    recommendations: Recommendation[];
    warnings: string[];
    next_review_minutes: number;
  };
  campaign_draft_ids: string[];
};

export function AgentCommandCenter() {
  const [command, setCommand] = useState("");
  const [running, setRunning] = useState(false);
  const [response, setResponse] = useState<CommandResponse | null>(null);
  const [error, setError] = useState("");

  async function submitCommand() {

    if (command.trim().length < 5) {
      setError("Describe what you want the AI Ads Team to accomplish.");
      return;
    }

    setRunning(true);
    setError("");
    setResponse(null);

    try {
      const request = await fetch(`${API_URL}/v1/command/runs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          command: command.trim(),
          mode: "shadow",
          create_campaign_draft: true,
          selected_agents: [
            "chief_strategy",
            "measurement_auditor",
            "budget_controller",
            "risk_controller",
          ],
        }),
      });

      const payload = await request.json();

      if (!request.ok) {
        throw new Error(
          typeof payload.detail === "string"
            ? payload.detail
            : "The agent run failed.",
        );
      }

      setResponse(payload as CommandResponse);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The agent run failed.",
      );
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="overflow-hidden rounded-3xl border border-[#1468F3]/15 bg-white shadow-[0_18px_50px_rgba(20,104,243,0.08)]">
      <div className="border-b border-neutral-200 bg-gradient-to-r from-[#1468F3]/[0.07] to-[#FF6500]/[0.05] p-6">
        <div className="flex items-start gap-4">
          <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#1468F3] text-white">
            <Bot className="h-6 w-6" />
          </span>

          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-black text-neutral-950">
                Command your AI Ads Team
              </h2>
              <Sparkles className="h-4 w-4 text-[#FF6500]" />
            </div>

            <p className="mt-1 text-sm leading-6 text-neutral-600">
              Describe the outcome you want. The specialist team will
              analyze, challenge and produce a protected shadow-mode plan.
            </p>
          </div>
        </div>

        <div className="mt-5">
          <div className="rounded-2xl border border-neutral-200 bg-white p-3 shadow-sm focus-within:border-[#1468F3]/50 focus-within:ring-4 focus-within:ring-[#1468F3]/10">
            <textarea
              value={command}
              onChange={(event) => setCommand(event.target.value)}
              placeholder="Example: Create a profitable Google Search campaign for my service with a $40 daily budget and strict CPA protection."
              rows={4}
              disabled={running}
              className="w-full resize-none border-0 bg-transparent px-2 py-2 text-base leading-7 text-neutral-950 outline-none placeholder:text-neutral-400"
            />

            <div className="flex flex-col gap-3 border-t border-neutral-100 pt-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2 text-xs font-semibold text-neutral-500">
                <span className="rounded-full bg-[#1468F3]/10 px-3 py-1.5 text-[#1468F3]">
                  Qwen specialist team
                </span>
                <span className="rounded-full bg-[#FF6500]/10 px-3 py-1.5 text-[#FF6500]">
                  Shadow mode
                </span>
              </div>

              <button
                type="button"
                onClick={submitCommand}
                disabled={running}
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-[#FF6500] px-5 py-3 text-sm font-black text-white transition hover:bg-[#E85B00] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {running ? (
                  <LoaderCircle className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                {running ? "Specialists reasoning…" : "Run AI Ads Team"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-3 border-b border-red-200 bg-red-50 p-5 text-sm text-red-700">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {response && (
        <div className="space-y-6 p-6">
          <div className="flex items-start gap-3 rounded-2xl bg-[#1468F3]/[0.06] p-5">
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-[#1468F3]" />
            <div>
              <p className="font-black text-neutral-950">
                Strategy run completed
              </p>
              <p className="mt-2 text-sm leading-6 text-neutral-700">
                {response.result.executive_summary}
              </p>
              <p className="mt-2 font-mono text-xs text-neutral-500">
                Run: {response.run_id}
              </p>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-black uppercase tracking-[0.12em] text-neutral-500">
              Diagnosis
            </h3>

            <ul className="mt-3 space-y-2">
              {response.result.diagnosis.map((item) => (
                <li
                  key={item}
                  className="rounded-xl border border-neutral-200 p-4 text-sm leading-6 text-neutral-700"
                >
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-black uppercase tracking-[0.12em] text-neutral-500">
              Recommended actions
            </h3>

            <div className="mt-3 grid gap-4 lg:grid-cols-2">
              {response.result.recommendations.map(
                (recommendation, index) => (
                  <article
                    key={`${recommendation.title}-${index}`}
                    className="rounded-2xl border border-neutral-200 p-5"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <h4 className="font-black text-neutral-950">
                        {recommendation.title}
                      </h4>

                      <span className="rounded-full bg-[#1468F3]/10 px-2.5 py-1 text-xs font-bold text-[#1468F3]">
                        {Math.round(
                          recommendation.confidence * 100,
                        )}
                        %
                      </span>
                    </div>

                    <p className="mt-3 text-sm leading-6 text-neutral-600">
                      {recommendation.rationale}
                    </p>

                    <div className="mt-4 border-t border-neutral-100 pt-4 text-xs leading-5 text-neutral-500">
                      <p>
                        <strong>Expected:</strong>{" "}
                        {recommendation.expected_impact}
                      </p>
                      <p className="mt-1">
                        <strong>Measure:</strong>{" "}
                        {recommendation.measurement}
                      </p>
                      <p className="mt-1">
                        <strong>Risk:</strong> {recommendation.risk}
                      </p>
                    </div>
                  </article>
                ),
              )}
            </div>
          </div>

          {response.campaign_draft_ids.length > 0 && (
            <p className="rounded-xl bg-[#FF6500]/10 p-4 text-sm font-bold text-[#C84F00]">
              {response.campaign_draft_ids.length} protected campaign
              draft(s) were saved. No advertising money was spent.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
