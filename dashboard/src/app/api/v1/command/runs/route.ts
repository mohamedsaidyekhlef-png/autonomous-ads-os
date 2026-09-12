import { generateText } from "ai";
import { NextResponse } from "next/server";

export const maxDuration = 60;

type CommandRequest = {
  command?: string;
  mode?: string;
};

export async function POST(request: Request) {
  const started = Date.now();

  try {
    const body = (await request.json()) as CommandRequest;
    const command = body.command?.trim();

    if (!command || command.length < 5) {
      return NextResponse.json(
        { detail: "Describe the campaign objective in at least five characters." },
        { status: 400 },
      );
    }

    const response = await generateText({
      model: process.env.AI_MODEL ?? "zai/glm-5.3-promo-50",
      system: [
        "You are the Autonomous Ads OS strategy team.",
        "Operate only in protected Shadow Mode.",
        "Never claim that you accessed a private advertising account.",
        "Never publish campaigns, modify budgets, or spend money.",
        "Clearly separate observations, assumptions, missing data, risks, and recommendations.",
        "Give concise, practical campaign recommendations with measurable success criteria.",
      ].join(" "),
      prompt: command,
    });

    const analysis = response.text.trim();

    return NextResponse.json({
      run_id: crypto.randomUUID(),
      status: "completed",
      mode: "shadow",
      elapsed_seconds: Math.max(1, Math.round((Date.now() - started) / 1000)),
      result: {
        executive_summary: analysis,
        diagnosis: [
          "This analysis was generated from the submitted prompt only.",
          "No private Google Ads data or live campaign metrics were accessed.",
          "Connect verified read-only account data before treating recommendations as account-specific.",
        ],
        recommendations: [
          {
            title: "Review the AI-generated shadow plan",
            rationale: analysis,
            expected_impact:
              "A safer campaign hypothesis that can be reviewed before implementation.",
            risk: "low",
            confidence: 0.7,
            measurement:
              "Validate conversion tracking, CTR, CPC, conversion rate, CPA, ROAS, and lead quality before making decisions.",
          },
        ],
      },
      warnings: [
        "Shadow Mode is active.",
        "No campaign was published.",
        "No budget was changed.",
        "No advertising money was spent.",
      ],
    });
  } catch (error) {
    console.error("Live AI analysis failed", error);

    return NextResponse.json(
      {
        detail:
          error instanceof Error
            ? `Live AI analysis failed: ${error.message}`
            : "Live AI analysis failed.",
      },
      { status: 500 },
    );
  }
}
