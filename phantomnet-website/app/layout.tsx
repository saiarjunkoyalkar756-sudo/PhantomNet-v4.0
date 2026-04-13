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
    default: "PhantomNet - Autonomous AI Cyber Defense for the Modern Enterprise",
    template: "%s | PhantomNet",
  },
  description: "PhantomNet delivers an AI-driven security operations platform that automatically detects, analyzes, and neutralizes cyber threats with unparalleled speed and precision. Secure your enterprise with real-time, self-healing cyber defense.",
  keywords: [
    "PhantomNet",
    "Cyber Defense",
    "AI Security",
    "Autonomous Security",
    "Enterprise Security",
    "SOC Automation",
    "Threat Detection",
    "Incident Response",
    "Zero Trust",
    "Blockchain Audit",
    "Cybersecurity",
    "SaaS",
  ],
  authors: [{ name: "PhantomNet Team" }],
  creator: "PhantomNet Team",
  publisher: "PhantomNet",
  openGraph: {
    title: "PhantomNet - Autonomous AI Cyber Defense for the Modern Enterprise",
    description: "PhantomNet delivers an AI-driven security operations platform that automatically detects, analyzes, and neutralizes cyber threats with unparalleled speed and precision. Secure your enterprise with real-time, self-healing cyber defense.",
    url: "https://www.phantomnet.com", // Replace with actual domain
    siteName: "PhantomNet",
    images: [
      {
        url: "https://www.phantomnet.com/og-image.jpg", // Replace with actual OG image
        width: 1200,
        height: 630,
        alt: "PhantomNet - AI-Driven Autonomous Cyber Defense",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "PhantomNet - Autonomous AI Cyber Defense for the Modern Enterprise",
    description: "PhantomNet delivers an AI-driven security operations platform that automatically detects, analyzes, and neutralizes cyber threats with unparalleled speed and precision. Secure your enterprise with real-time, self-healing cyber defense.",
    creator: "@PhantomNetAI", // Replace with actual Twitter handle
    images: ["https://www.phantomnet.com/twitter-image.jpg"], // Replace with actual Twitter image
  },
  // Additional SEO considerations
  metadataBase: new URL("https://www.phantomnet.com"), // Replace with actual domain
  alternates: {
    canonical: "https://www.phantomnet.com", // Replace with actual domain
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
