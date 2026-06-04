"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import { healthReportApi, HealthReport } from "@/lib/api";
import { getToken, getUser } from "@/lib/auth";

const MONTHS = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"];

export default function HealthReportsPage() {
  const router = useRouter();

  const [reports, setReports] = useState<HealthReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const [selectedYear, setSelectedYear] = useState(0);
  const [selectedMonth, setSelectedMonth] = useState(0);

  useEffect(() => {
    const now = new Date();
    setSelectedYear(now.getFullYear());
    setSelectedMonth(now.getMonth() + 1);
  }, []);

  const load = useCallback(() => {
    healthReportApi.list()
      .then(({ data }) => setReports(data))
      .catch(() => toast.error("리포트를 불러오지 못했어요."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    if (getUser()?.role !== "PATIENT") { router.replace("/dashboard"); return; }
    load();
  }, [router, load]);

  async function handleGenerate() {
    setGenerating(true);
    try {
      const { data } = await healthReportApi.generate(selectedYear, selectedMonth);
      toast.success(`${selectedYear}년 ${selectedMonth}월 리포트가 생성됐어요.`);
      setReports((prev) => {
        const filtered = prev.filter((r) => !(r.year === data.year && r.month === data.month));
        return [data, ...filtered].sort((a, b) => b.year - a.year || b.month - a.month);
      });
      setExpandedId(data.id);
    } catch {
      toast.error("리포트 생성에 실패했어요.");
    } finally {
      setGenerating(false);
    }
  }

  const years = selectedYear > 0
    ? Array.from({ length: 3 }, (_, i) => selectedYear - i)
    : [];

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">월별 건강 리포트</h1>
            <p className="text-sm text-zinc-500 mt-1">AI가 이달의 건강 데이터를 분석해 리포트를 작성해요.</p>
          </div>
        </div>

        {/* 생성 패널 */}
        <div className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 rounded-2xl p-5 mb-6 flex flex-col sm:flex-row gap-3 items-end">
          <div className="flex-1">
            <p className="text-xs font-semibold text-zinc-500 dark:text-zinc-400 mb-2">리포트 기간 선택</p>
            <div className="flex gap-2">
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(Number(e.target.value))}
                className="flex-1 rounded-lg border border-zinc-200 dark:border-zinc-600 bg-white dark:bg-zinc-700 text-zinc-800 dark:text-zinc-200 px-3 py-2 text-sm"
              >
                {years.map((y) => <option key={y} value={y}>{y}년</option>)}
              </select>
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(Number(e.target.value))}
                className="flex-1 rounded-lg border border-zinc-200 dark:border-zinc-600 bg-white dark:bg-zinc-700 text-zinc-800 dark:text-zinc-200 px-3 py-2 text-sm"
              >
                {MONTHS.map((label, i) => <option key={i + 1} value={i + 1}>{label}</option>)}
              </select>
            </div>
          </div>
          <Button
            onClick={handleGenerate}
            disabled={generating}
            className="bg-blue-700 hover:bg-blue-800 shrink-0"
          >
            {generating ? "생성 중..." : "✨ AI 리포트 생성"}
          </Button>
        </div>

        {/* 리포트 목록 */}
        {loading && (
          <div className="space-y-3">
            {[1, 2].map((i) => <div key={i} className="h-20 rounded-xl bg-zinc-200 dark:bg-zinc-800 animate-pulse" />)}
          </div>
        )}

        {!loading && reports.length === 0 && (
          <div className="text-center py-20 text-zinc-400">
            <p className="text-5xl mb-4">📋</p>
            <p className="text-lg font-medium">아직 리포트가 없어요</p>
            <p className="text-sm mt-1">위에서 기간을 선택하고 첫 리포트를 생성해보세요.</p>
          </div>
        )}

        <div className="space-y-3">
          {reports.map((report) => {
            const isExpanded = expandedId === report.id;
            return (
              <div
                key={report.id}
                className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 rounded-xl overflow-hidden"
              >
                <button
                  className="w-full flex items-center justify-between px-5 py-4 text-left"
                  onClick={() => setExpandedId(isExpanded ? null : report.id)}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">📋</span>
                    <div>
                      <p className="font-semibold text-zinc-900 dark:text-zinc-100">
                        {report.year}년 {report.month}월 건강 리포트
                      </p>
                      <p className="text-xs text-zinc-400 mt-0.5">
                        {new Date(report.created_at).toLocaleString("ko-KR")}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {report.status === "COMPLETED" && (
                      <span className="text-xs bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full">완료</span>
                    )}
                    {report.status === "FAILED" && (
                      <span className="text-xs bg-red-50 dark:bg-red-900/20 text-red-500 px-2 py-0.5 rounded-full">실패</span>
                    )}
                    <span className="text-zinc-400 text-sm">{isExpanded ? "▲" : "▼"}</span>
                  </div>
                </button>

                {isExpanded && report.status === "COMPLETED" && report.report_text && (
                  <div className="px-5 pb-5 border-t border-zinc-100 dark:border-zinc-700">
                    <div className="pt-4 prose prose-sm dark:prose-invert max-w-none text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap leading-relaxed text-sm">
                      {report.report_text}
                    </div>
                    <button
                      onClick={() => {
                        const win = window.open("", "_blank");
                        if (!win) return;
                        win.document.write(`<!DOCTYPE html><html lang="ko"><head>
                          <meta charset="UTF-8"><title>${report.year}년 ${report.month}월 건강 리포트</title>
                          <style>
                            body{font-family:'Apple SD Gothic Neo',sans-serif;max-width:700px;margin:40px auto;padding:0 24px;color:#1a1a1a;line-height:1.8}
                            h1{color:#1d4ed8;border-bottom:2px solid #1d4ed8;padding-bottom:8px}
                            h2,h3{color:#374151}
                            pre{white-space:pre-wrap;word-break:break-word}
                            @media print{@page{margin:20mm}}
                          </style>
                        </head><body>
                          <h1>${report.year}년 ${report.month}월 건강 리포트</h1>
                          <pre>${(report.report_text ?? "").replace(/</g,"&lt;")}</pre>
                          <p style="color:#9ca3af;font-size:12px;margin-top:40px">생성일: ${new Date(report.created_at).toLocaleString("ko-KR")}</p>
                        </body></html>`);
                        win.document.close();
                        win.print();
                      }}
                      className="mt-4 text-xs text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      📄 PDF로 저장하기
                    </button>
                  </div>
                )}

                {isExpanded && report.status === "FAILED" && (
                  <div className="px-5 pb-5 border-t border-zinc-100 dark:border-zinc-700">
                    <p className="pt-4 text-sm text-red-500">리포트 생성에 실패했어요. 다시 생성해보세요.</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
