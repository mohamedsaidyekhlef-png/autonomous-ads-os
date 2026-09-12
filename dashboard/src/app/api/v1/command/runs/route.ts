import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const MODEL = "llama-3.3-70b-versatile";
const GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions";

type CommandRequest = {
  command?: string;
  mode?: string;
};

type Recommendation = {
  title: string;
  rationale: string;
  expected_impact: string;
  risk: string;
  confidence: number;
  measurement: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function text(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function textList(value: unknown, fallback: string[]): string[] {
  if (!Array.isArray(value)) return fallback;

  const values = value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean);

  return values.length ? values : fallback;
}

function recommendation(value: unknown, index: number): Recommendation {
  const item = isRecord(value) ? value : {};
  const rawConfidence =
    typeof item.confidence === "number" ? item.confidence : 0.7;

  const confidence =
    rawConfidence > 1
      ? Math.min(1, rawConfidence / 100)
      : Math.max(0, Math.min(1, rawConfidence));

  return {
    title: text(item.title, `Recommendation ${index + 1}`),
    rationale: text(
      item.rationale,
      "Review this recommendation against verified campaign data.",
    ),
    expected_impact: text(
      item.expected_impact,
      "Improved campaign clarity and measurement readiness.",
    ),
    risk: text(item.risk, "medium"),
    confidence,
    measurement: text(
      item.measurement,
      "Track CTR, conversion rate, CPA, ROAS, and qualified lead volume.",
    ),
  };
}

export async function GET() {
  return NextResponse.json({
    status: "ready",
    version: "groq-live-v2",
    provider: "groq",
    model: MODEL,
    mode: "shadow",
    dry_run: true,
    configured: Boolean(process.env.GROQ_API_KEY),
  });
}

export async function POST(request: Request) {
  const started = Date.now();

  try {
    const apiKey = process.env.GROQ_API_KEY;

    if (!apiKey) {
      return NextResponse.json(
        { detail: "The live AI service is not configured." },
        { status: 503 },
      );
    }

    const body = (await request.json()) as CommandRequest;
    const command = body.command?.trim();

    if (!command || command.length < 5) {
      return NextResponse.json(
        { detail: "Describe the campaign objective in at least five characters." },
        { status: 400 },
      );
    }

    if (command.length > 6000) {
      return NextResponse.json(
        { detail: "The campaign request must be 6,000 characters or fewer." },
        { status: 400 },
      );
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 55_000);

    let providerResponse: Response;

    try {
      providerResponse = await fetch(GROQ_ENDPOINT, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        signal: controller.signal,
        body: JSON.stringify({
          model: MODEL,
          temperature: 0.35,
          max_completion_tokens: 2200,
          messages: [
            {
              role: "system",
              content: [
                "You are the Autonomous Ads OS multi-agent advertising strategy team.",
                "Operate exclusively in protected Shadow Mode.",
                "Never publish, pause, edit, or create a live advertising campaign.",
                "Never change a budget, bid, audience, creative, account, or payment setting.",
                "Never claim access to private advertising data unless the user supplied it.",
                "Never invent campaign metrics.",
                "Clearly label assumptions and missing information.",
                "Return only valid JSON.",
                "Use this exact structure:",
                '{"executive_summary":"string","diagnosis":["string"],"assumptions":["string"],"missing_information":["string"],"recommendations":[{"title":"string","rationale":"string","expected_impact":"string","risk":"low|medium|high","confidence":0.0,"measurement":"string"}]}',
              ].join(" "),
            },
            {
              role: "user",
              content: [
                "Analyze the following advertising request:",
                command,
                "",
                "Produce a practical campaign strategy including targeting, campaign structure,",
                "keywords or audiences where applicable, negative targeting, creative direction,",
                "landing-page guidance, measurement requirements, risks, and next steps.",
                "Do not perform any live action.",
              ].join("\n"),
            },
          ],
        }),
      });
    } finally {
      clearTimeout(timeout);
    }

    if (!providerResponse.ok) {
      if (providerResponse.status === 429) {
        return NextResponse.json(
          { detail: "The AI service is temporarily rate limited. Try again shortly." },
          { status: 429 },
        );
      }

      if (providerResponse.status === 401 || providerResponse.status === 403) {
        return NextResponse.json(
          { detail: "The AI service credentials require attention." },
          { status: 503 },
        );
      }

      const providerError = await providerResponse.text();
      console.error(
        "Groq request failed",
        providerResponse.status,
        providerError.slice(0, 1000),
      );

      return NextResponse.json(
        { detail: "The AI provider could not complete this analysis." },
        { status: 502 },
      );
    }

    const providerPayload = (await providerResponse.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };

    const rawContent = providerPayload.choices?.[0]?.message?.content?.trim();

    if (!rawContent) {
      throw new Error("The AI provider returned an empty response.");
    }

    const cleanedContent = rawContent
      .replace(/^```json\s*/i, "")
      .replace(/```$/i, "")
      .trim();

    const decoded = JSON.parse(cleanedContent) as unknown;
    const result = isRecord(decoded) ? decoded : {};

    const rawRecommendations = Array.isArray(result.recommendations)
      ? result.recommendations
      : [];

    const recommendations = rawRecommendations
      .slice(0, 8)
      .map(recommendation);

    if (!recommendations.length) {
      recommendations.push(
        recommendation(
          {
            title: "Validate the campaign plan",
            rationale:
              "The proposed strategy must be checked against verified account and conversion data.",
            expected_impact:
              "Reduced launch risk and more reliable optimization decisions.",
            risk: "low",
            confidence: 0.65,
            measurement:
              "Confirm conversion tracking, CPA targets, ROAS targets, and lead quality.",
          },
          0,
        ),
      );
    }

    return NextResponse.json({
      run_id: crypto.randomUUID(),
      status: "completed",
      provider: "groq",
      model: MODEL,
      mode: "shadow",
      dry_run: true,
      elapsed_seconds: Math.max(1, Math.round((Date.now() - started) / 1000)),
      result: {
        executive_summary: text(
          result.executive_summary,
          "The AI completed a protected campaign analysis.",
        ),
        diagnosis: textList(result.diagnosis, [
          "No private advertising-account data was supplied.",
          "Recommendations require validation against real conversion data.",
        ]),
        assumptions: textList(result.assumptions, [
          "The request is for strategic planning in Shadow Mode.",
        ]),
        missing_information: textList(result.missing_information, [
          "Verified conversion tracking and historical campaign performance.",
        ]),
        recommendations,
      },
      warnings: [
        "Shadow Mode is active.",
        "No campaign was published or modified.",
        "No budget was changed.",
        "No advertising money was spent.",
      ],
    });
  } catch (error) {
    console.error("Live Groq analysis failed", error);

    const timedOut =
      error instanceof Error && error.name === "AbortError";

    return NextResponse.json(
      {
        detail: timedOut
          ? "The AI analysis timed out. Try a shorter campaign request."
          : "The AI response could not be validated. Please try again.",
      },
      { status: timedOut ? 504 : 500 },
    );
  }
}
