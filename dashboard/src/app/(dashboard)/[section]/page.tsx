import { notFound } from "next/navigation";

import { SectionRouter } from "@/components/section-pages";
import { CampaignAnalysis } from "@/components/campaign-analysis";
import { ExpertReviewWorkspace } from "@/components/workspaces/expert-review-workspace";

const validSections = new Set([
  "connections",
  "campaigns",
  "campaign-analysis",
  "expert-reviews",
  "agents",
  "decisions",
  "experiments",
  "creative",
  "reports",
  "notifications",
  "settings",
]);

export default async function SectionPage({
  params,
}: {
  params: Promise<{ section: string }>;
}) {
  const { section } = await params;

  if (!validSections.has(section)) {
    notFound();
  }

  if (section === "campaign-analysis") {
    return <CampaignAnalysis />;
  }

  if (section === "expert-reviews") {
    return <ExpertReviewWorkspace />;
  }

  return <SectionRouter section={section} />;
}
