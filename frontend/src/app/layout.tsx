import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Playfair_Display } from "next/font/google";
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

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "BrandGuard — High-Fashion Review Intelligence & Deterministic Audit Engine",
  description:
    "Award-winning editorial B2B review intelligence SaaS platform. High-fashion dark editorial aesthetics powered by DeBERTa-v3 ABSA, HDBSCAN micro-theme induction, STL+EWMA control charts, and zero-hallucination hybrid RAG.",
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
    <html
      lang="en"
      className={`dark ${inter.variable} ${jetbrainsMono.variable} ${playfair.variable}`}
    >
      <body className="min-h-screen bg-[#0A1128] text-[#FAF6F0] antialiased selection:bg-[#FF5A36]/30 selection:text-white font-sans overflow-x-hidden">
        {children}
      </body>
    </html>
  );
}
