import type { Metadata } from "next";
import "./globals.css";
import { BrandLaunch } from "@/components/brand-launch";

export const metadata: Metadata = {
  title: "Autonomous Ads OS",
  description: "Your autonomous performance marketing department",
  manifest: "/manifest.webmanifest",
  icons: {
    icon: "/brand-logo.png",
    shortcut: "/brand-logo.png",
    apple: "/brand-logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <BrandLaunch />{children}</body>
    </html>
  );
}
