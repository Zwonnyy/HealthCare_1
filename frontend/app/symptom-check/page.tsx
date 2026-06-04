"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { symptomCheckApi, type SymptomCheck, type UrgencyLevel } from "@/lib/api";

const URGENCY_CONFIG: Record<UrgencyLevel, { label: string; color: string; bg: string }> = {
  HIGH: { label: "높음 — 즉시 진료 필요", color: "text-red-700 dark:text-red-400", bg: "bg-red-50 border-red-300 dark:bg-red-950/30 dark:border-red-700" },
  MEDIUM: { label: "중간 — 48시간 내 진료 권고", color: "text-amber-700 dark:text-amber-400", bg: "bg-amber-50 border-amber-300 dark:bg-amber-950/30 dark:border-amber-700" },
  LOW: { label: "낮음 — 자가 관리 가능", color: "text-green-700 dark:text-green-400", bg: "bg-green-50 border-green-300 dark:bg-green-950/30 dark:border-green-700" },
};

const EXAMPLE_SYMPTOMS = [
  "3일째 두통이 있고 목도 뻣뻣해요",
  "가슴이 답답하고 숨이 차요",
  "식후에 명치가 쓰리고 속이 메스꺼워요",
  "무릎이 붓고 계단 오를 때 통증이 심해요",
];

export default function SymptomCheckPage() {
  const router = useRouter();
  const [symptomText, setSymptomText] = useState("");
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState<SymptomCheck | null>(null);
  const [history, setHistory] = useState<SymptomCheck[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const fetchHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const res = await symptomCheckApi.list();
      setHistory(res.data);
    } catch {
      /* ignore */
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  async function handleCheck() {
    if (!symptomText.trim()) {
      toast.error("증상을 입력해주세요.");
      return;
    }
    setChecking(true);
    setResult(null);
    try {
      const res = await symptomCheckApi.check(symptomText.trim());
      setResult(res.data);
      setHistory((prev) => [res.data, ...prev]);
    } catch {
      toast.error("AI 분석에 실패했어요. 다시 시도해주세요.");
    } finally {
      setChecking(false);
    }
  }

  function handleBook() {
    router.push("/appointments");
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleString("ko-KR", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  }

  const urgencyInfo = result?.urgency ? URGENCY_CONFIG[result.urgency] : null;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">AI 증상 체크</h1>
        <p className="text-sm text-zinc-500 mt-1">증상을 입력하면 AI가 긴급도를 평가하고 진료 여부를 안내해요.</p>
      </div>

      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-6 space-y-4">
        <div className="space-y-2">
          <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">증상을 자세히 설명해주세요</p>
          <textarea
            rows={4}
            value={symptomText}
            onChange={(e) => setSymptomText(e.target.value)}
            placeholder="예: 3일째 두통이 있고 목이 뻣뻣해요. 열은 없지만 빛에 민감한 것 같아요."
            className="w-full rounded-lg border border-zinc-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_SYMPTOMS.map((s) => (
            <button
              key={s}
              onClick={() => setSymptomText(s)}
              className="text-xs px-2 py-1 rounded-full border border-zinc-200 dark:border-zinc-600 text-zinc-500 dark:text-zinc-400 hover:border-blue-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
        <Button onClick={handleCheck} disabled={checking} className="w-full bg-blue-700 hover:bg-blue-800">
          {checking ? "AI 분석 중..." : "🔍 증상 분석하기"}
        </Button>
      </div>

      {result && urgencyInfo && (
        <div className={`rounded-xl border p-5 space-y-4 ${urgencyInfo.bg}`}>
          <div className="flex items-center gap-3">
            <span className="text-2xl">{result.urgency === "HIGH" ? "🚨" : result.urgency === "MEDIUM" ? "⚠️" : "✅"}</span>
            <div>
              <p className="text-xs text-zinc-500">긴급도</p>
              <p className={`font-semibold ${urgencyInfo.color}`}>{urgencyInfo.label}</p>
            </div>
          </div>
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <p className="text-sm text-zinc-700 dark:text-zinc-300 whitespace-pre-line">{result.ai_assessment}</p>
          </div>
          {result.suggest_appointment && (
            <Button onClick={handleBook} className="bg-blue-700 hover:bg-blue-800">
              진료 예약하기 →
            </Button>
          )}
        </div>
      )}

      {history.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-zinc-800 dark:text-zinc-200">이전 기록</h2>
          {loadingHistory && <p className="text-sm text-zinc-400">불러오는 중...</p>}
          {history.slice(result ? 1 : 0).map((c) => {
            const uInfo = c.urgency ? URGENCY_CONFIG[c.urgency] : null;
            return (
              <div key={c.id} className="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300 line-clamp-1">{c.symptom_text}</p>
                  <span className="text-xs text-zinc-400 ml-2 shrink-0">{formatDate(c.created_at)}</span>
                </div>
                {uInfo && (
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${uInfo.bg} ${uInfo.color}`}>
                    {uInfo.label}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
