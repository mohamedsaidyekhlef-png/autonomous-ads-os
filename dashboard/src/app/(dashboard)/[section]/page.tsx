import { notFound } from "next/navigation";

import { SectionRouter } from "@/components/section-pages";
import { CampaignAnalysis } from "@/components/campaign-analysis";

const validSections = new Set([
  "connections",
  "campaigns",
  "campaign-analysis",
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

  return <SectionRouter section={section} />;
}
