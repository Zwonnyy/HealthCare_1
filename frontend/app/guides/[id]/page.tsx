"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import { guideApi, Guide } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function GuideDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [guide, setGuide] = useState<Guide | null>(null);

  useEffect(() => {
    if (!getToken()) { router.push("/login"); return; }
    guideApi.get(Number(id))
      .then(({ data }) => setGuide(data))
      .catch(() => { toast.error("가이드를 불러오지 못했어요."); router.back(); });
  }, [id, router]);

  if (!guide) {
    return (
      <div className="min-h-screen bg-zinc-50">
        <Navbar />
        <div className="max-w-3xl mx-auto px-4 py-16 space-y-3">
          {[1, 2].map((i) => <div key={i} className="h-48 rounded-xl bg-zinc-200 animate-pulse" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-10 space-y-6">

        <div className="flex items-center gap-3">
          <Link href={`/records/${guide.record_id}`}>
            <Button variant="ghost" size="sm" className="text-zinc-500 hover:text-zinc-800 -ml-2">
              ← 진료 기록으로
            </Button>
          </Link>
        </div>

        {/* 상단 배너 */}
        <div className="rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
          <p className="text-blue-100 text-sm mb-1">Claude AI 생성</p>
          <h1 className="text-2xl font-bold">맞춤 복약 & 생활습관 가이드</h1>
          <p className="text-blue-200 text-xs mt-2">
            생성일: {new Date(guide.created_at).toLocaleString("ko-KR")}
          </p>
        </div>

        {/* 복약 안내 */}
        {guide.medication_guide && (
          <div className="bg-white rounded-2xl border border-zinc-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-zinc-50 flex items-center gap-2">
              <span className="text-xl">💊</span>
              <h2 className="font-bold text-zinc-900">복약 안내</h2>
            </div>
            <div className="px-6 py-5">
              <div className="prose prose-sm prose-zinc max-w-none
                prose-headings:font-semibold prose-headings:text-zinc-800
                prose-p:text-zinc-600 prose-p:leading-relaxed
                prose-li:text-zinc-600 prose-li:leading-relaxed
                prose-strong:text-zinc-800
                prose-h3:text-base prose-h2:text-lg">
                <ReactMarkdown>{guide.medication_guide}</ReactMarkdown>
              </div>
            </div>
          </div>
        )}

        {/* 생활습관 가이드 */}
        {guide.lifestyle_guide && (
          <div className="bg-white rounded-2xl border border-zinc-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-zinc-50 flex items-center gap-2">
              <span className="text-xl">🏃</span>
              <h2 className="font-bold text-zinc-900">생활습관 개선 가이드</h2>
            </div>
            <div className="px-6 py-5">
              <div className="prose prose-sm prose-zinc max-w-none
                prose-headings:font-semibold prose-headings:text-zinc-800
                prose-p:text-zinc-600 prose-p:leading-relaxed
                prose-li:text-zinc-600 prose-li:leading-relaxed
                prose-strong:text-zinc-800
                prose-h3:text-base prose-h2:text-lg">
                <ReactMarkdown>{guide.lifestyle_guide}</ReactMarkdown>
              </div>
            </div>
          </div>
        )}

        {/* 면책 고지 */}
        <div className="rounded-xl bg-amber-50 border border-amber-100 px-5 py-4 flex gap-3">
          <span className="text-lg shrink-0">⚠️</span>
          <p className="text-xs text-amber-700 leading-relaxed">
            이 가이드는 <b>Claude AI</b>가 진료 기록을 기반으로 생성한 참고 정보입니다.
            실제 의료 결정은 반드시 담당 의사와 상담하시기 바랍니다.
            약물 부작용이나 이상 반응 발생 시 즉시 의료진에게 연락하세요.
          </p>
        </div>
      </main>
    </div>
  );
}