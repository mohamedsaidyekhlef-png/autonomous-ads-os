import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";

const baseURL = "http://127.0.0.1:3099";
const outputDirectory = path.resolve(process.cwd(), "../docs/screenshots");

await fs.mkdir(outputDirectory, { recursive: true });

const safeCompletedRun = {
  run_id: "00000000-0000-4000-8000-000000000001",
  status: "completed",
  mode: "shadow",
  elapsed_seconds: 18,
  error_message: null,
  result: {
    executive_summary:
      "The account is ready for a measurement-first campaign draft. No advertising changes or spending were performed.",
    diagnosis: [
      "Conversion tracking should be validated before campaign activation.",
      "Budget allocation remains protected by mandatory Shadow Mode."
    ],
    recommendations: [
      {
        title: "Validate primary conversion events",
        rationale:
          "Reliable conversion signals are required before optimization decisions can be trusted.",
        expected_impact: "Higher measurement confidence",
        risk: "Low",
        confidence: 0.94,
        measurement: "Verified conversion-event coverage"
      },
      {
        title: "Prepare a controlled search campaign draft",
        rationale:
          "A narrow draft creates a reviewable starting point without changing a live advertising account.",
        expected_impact: "Faster launch preparation",
        risk: "Low",
        confidence: 0.88,
        measurement: "Draft quality and approval readiness"
      }
    ]
  }
};

const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1,
    colorScheme: "light"
  });

  const page = await context.newPage();

  await page.goto(`${baseURL}/overview`, {
    waitUntil: "domcontentloaded"
  });

  await page.evaluate(() => {
    window.localStorage.removeItem("ads-os:last-run");
  });

  await page.reload({ waitUntil: "domcontentloaded" });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1200);

  await page.screenshot({
    path: path.join(outputDirectory, "overview.png"),
    fullPage: true
  });

  await page.evaluate((run) => {
    window.localStorage.setItem("ads-os:last-run", JSON.stringify(run));
  }, safeCompletedRun);

  await page.reload({ waitUntil: "domcontentloaded" });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1200);

  const commandCenter = page
    .locator("section")
    .filter({ hasText: "Command your AI Ads Team" })
    .first();

  await commandCenter.waitFor({ state: "visible" });

  await commandCenter.screenshot({
    path: path.join(outputDirectory, "command-center.png")
  });

  await page.goto(`${baseURL}/connections`, {
    waitUntil: "domcontentloaded"
  });

  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1200);

  await page.screenshot({
    path: path.join(outputDirectory, "connections.png"),
    fullPage: true
  });

  console.log("Created:");
  console.log("docs/screenshots/overview.png");
  console.log("docs/screenshots/command-center.png");
  console.log("docs/screenshots/connections.png");
} finally {
  await browser.close();
}
