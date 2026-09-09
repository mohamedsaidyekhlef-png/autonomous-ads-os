import { notFound } from "next/navigation";

import { SectionRouter } from "@/components/section-pages";

const validSections = new Set([
  "connections",
  "campaigns",
  "agents",
  "decisions",
  "experiments",
  "creative",
  "reports",
  "notifications",
  "billing",
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

  return <SectionRouter section={section} />;
}
