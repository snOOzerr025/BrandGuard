import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "BrandGuard — Deterministic Review Intelligence Engine",
  description:
    "Enterprise decision-grade review intelligence SaaS platform powered by DeBERTa-v3 ABSA, HDBSCAN micro-theme induction, STL+EWMA control charts, and zero-hallucination hybrid RAG.",
  keywords: [
    "BrandGuard",
    "Review Intelligence",
    "ABSA",
    "DeBERTa",
    "Customer Sentiment",
    "Enterprise SaaS",
    "RAG",
    "Anomaly Detection",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-[#0D0E10] text-[#FFFFFF] antialiased selection:bg-[#10B981]/30 selection:text-white font-sans overflow-x-hidden">
        {children}
      </body>
    </html>
  );
}
