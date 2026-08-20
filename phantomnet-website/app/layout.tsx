import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google"; // Import custom fonts
import "./globals.css";
import { Header } from "@/components/Header"; // Import Header
import { Footer } from "@/components/Footer"; // Import Footer
import { cn } from "@/lib/utils"; // Import cn utility for class merging

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
});

export const metadata: Metadata = {
  title: {
    default: "PhantomNet - Evidence-First Self-Hosted SOC",
    template: "%s | PhantomNet",
  },
  description: "PhantomNet is an evidence-first self-hosted SOC foundation with canonical telemetry, governed detection, analyst workflows, and approval-bound response.",
  keywords: [
    "PhantomNet",
    "Cyber Defense",
    "Self-Hosted SOC",
    "Governed Response",
    "Detection Engineering",
    "SOC Automation",
    "Threat Detection",
    "Incident Response",
    "Zero Trust",
    "Tamper-Evident Audit",
    "Cybersecurity",
    "Open Security Operations",
  ],
  authors: [{ name: "PhantomNet Contributors" }],
  publisher: "PhantomNet",
  openGraph: {
    title: "PhantomNet - Evidence-First Self-Hosted SOC",
    description: "PhantomNet is an evidence-first self-hosted SOC foundation with canonical telemetry, governed detection, analyst workflows, and approval-bound response.",
    siteName: "PhantomNet",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "PhantomNet - Evidence-First Self-Hosted SOC",
    description: "PhantomNet is an evidence-first self-hosted SOC foundation with canonical telemetry, governed detection, analyst workflows, and approval-bound response.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={cn(
          "min-h-screen bg-background font-sans antialiased",
          inter.variable,
          spaceGrotesk.variable
        )}
      >
        <Header />
        <main className="flex-grow">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
