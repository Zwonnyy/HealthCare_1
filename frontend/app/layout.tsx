import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";

const geist = Geist({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "진료 기록 기반 복약 안내 시스템",
  description: "AI 기반 복약 안내 및 생활습관 개선 가이드",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className="h-full">
      <body className={`${geist.className} min-h-full bg-zinc-50`}>
        {children}
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
