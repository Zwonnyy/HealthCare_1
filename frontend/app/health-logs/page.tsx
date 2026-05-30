"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import Navbar from "@/components/Navbar";
import { healthLogApi, HealthLog, Mood } from "@/lib/api";
import { getToken, getUser } from "@/lib/auth";

const MOOD_OPTIONS: { value: Mood; label: string; emoji: string }[] = [
  { value: "GREAT", label: "매우 좋음", emoji: "😄" },
  { value: "GOOD", label: "좋음", emoji: "🙂" },
  { value: "NORMAL", label: "보통", emoji: "😐" },
  { value: "BAD", label: "나쁨", emoji: "😕" },
  { value: "TERRIBLE", label: "매우 나쁨", emoji: "😢" },
];

function moodEmoji(mood: Mood) {
  return MOOD_OPTIONS.find((m) => m.value === mood)?.emoji ?? "😐";
}

function moodLabel(mood: Mood) {
  return MOOD_OPTIONS.find((m) => m.value === mood)?.label ?? mood;
}

export default function HealthLogsPage() {
  const router = useRouter();
  const user = getUser();

  const [logs, setLogs] = useState<HealthLog[]>([]);
  const [loading, setLoading] = useState(true);

  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    log_date: new Date().toISOString().slice(0, 10),
    pain_score: 5,
    mood: "NORMAL" as Mood,
    symptoms_text: "",
    notes: "",
  });

  const [analyzing, setAnalyzing] = useState(false);

  const loadLogs = useCallback(() => {
    setLoading(true);
    healthLogApi
      .list()
      .then(({ data }) => setLogs(data.items))
      .catch(() => toast.error("건강 일지를 불러오지 못했어요."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    if (user?.role !== "PATIENT") { router.replace("/records"); return; }
    loadLogs();
  }, [router, loadLogs]);

  async function handleCreate() {
    if (!form.symptoms_text.trim()) { toast.error("증상을 입력해주세요."); return; }
    setSubmitting(true);
    try {
      await healthLogApi.create({
        log_date: form.log_date,
        pain_score: form.pain_score,
        mood: form.mood,
        symptoms_text: form.symptoms_text.trim(),
        notes: form.notes.trim() || undefined,
      });
      toast.success("건강 일지를 저장했어요.");
      setShowModal(false);
      setForm({
        log_date: new Date().toISOString().slice(0, 10),
        pain_score: 5,
        mood: "NORMAL",
        symptoms_text: "",
        notes: "",
      });
      loadLogs();
    } catch {
      toast.error("저장에 실패했어요.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("정말 삭제할까요?")) return;
    try {
      await healthLogApi.delete(id);
      toast.success("삭제됐어요.");
      setLogs((prev) => prev.filter((l) => l.id !== id));
    } catch {
      toast.error("삭제에 실패했어요.");
    }
  }

  async function handleAnalyze() {
    setAnalyzing(true);
    try {
      await healthLogApi.requestAnalysis();
      toast.success("AI 분석을 요청했어요. 완료되면 알림을 드려요.");
    } catch {
      toast.error("분석 요청에 실패했어요.");
    } finally {
      setAnalyzing(false);
    }
  }

  function painColor(score: number) {
    if (score <= 3) return "text-green-600";
    if (score <= 6) return "text-amber-500";
    return "text-red-500";
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900">건강 일지</h1>
            <p className="text-sm text-zinc-500 mt-1">
              매일 컨디션을 기록하고 AI 분석을 받아보세요.
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleAnalyze}
              disabled={analyzing}
            >
              {analyzing ? "요청 중…" : "📊 AI 분석 요청"}
            </Button>
            <Button
              className="bg-blue-700 hover:bg-blue-800"
              onClick={() => setShowModal(true)}
            >
              + 기록 추가
            </Button>
          </div>
        </div>

        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 rounded-xl bg-zinc-200 animate-pulse" />
            ))}
          </div>
        )}

        {!loading && logs.length === 0 && (
          <div className="text-center py-20 text-zinc-400">
            <p className="text-5xl mb-4">📓</p>
            <p className="text-lg font-medium">건강 일지가 없어요</p>
            <Button
              className="mt-4 bg-blue-700 hover:bg-blue-800"
              onClick={() => setShowModal(true)}
            >
              첫 기록 작성하기
            </Button>
          </div>
        )}

        <div className="space-y-3">
          {logs.map((log) => (
            <div
              key={log.id}
              className="bg-white border border-zinc-100 rounded-xl p-5"
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{moodEmoji(log.mood)}</span>
                    <span className="text-sm font-medium text-zinc-700">{moodLabel(log.mood)}</span>
                    <Badge variant="secondary" className="text-xs">{log.log_date}</Badge>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-sm font-bold ${painColor(log.pain_score)}`}>
                      통증 {log.pain_score}/10
                    </span>
                  </div>
                  <p className="text-sm text-zinc-600 line-clamp-2 mt-1">{log.symptoms_text}</p>
                  {log.notes && (
                    <p className="text-xs text-zinc-400 line-clamp-1">메모: {log.notes}</p>
                  )}
                </div>
                <button
                  onClick={() => handleDelete(log.id)}
                  className="ml-4 shrink-0 text-xs text-zinc-400 hover:text-red-500 transition-colors"
                >
                  삭제
                </button>
              </div>
            </div>
          ))}
        </div>

        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
              <h2 className="text-lg font-bold text-zinc-900 mb-4">건강 일지 기록</h2>

              <div className="space-y-4">
                <div>
                  <Label className="mb-1.5">날짜</Label>
                  <Input
                    type="date"
                    value={form.log_date}
                    onChange={(e) => setForm({ ...form, log_date: e.target.value })}
                  />
                </div>

                <div>
                  <Label className="mb-1.5">통증 점수: {form.pain_score} / 10</Label>
                  <input
                    type="range"
                    min={0}
                    max={10}
                    step={1}
                    value={form.pain_score}
                    onChange={(e) => setForm({ ...form, pain_score: Number(e.target.value) })}
                    className="w-full accent-blue-600"
                  />
                  <div className="flex justify-between text-xs text-zinc-400 mt-1">
                    <span>0 (없음)</span>
                    <span>10 (극심)</span>
                  </div>
                </div>

                <div>
                  <Label className="mb-1.5">기분</Label>
                  <div className="flex gap-2 flex-wrap">
                    {MOOD_OPTIONS.map((m) => (
                      <button
                        key={m.value}
                        onClick={() => setForm({ ...form, mood: m.value })}
                        className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                          form.mood === m.value
                            ? "border-blue-500 bg-blue-50 text-blue-700"
                            : "border-zinc-200 text-zinc-600 hover:border-zinc-300"
                        }`}
                      >
                        {m.emoji} {m.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <Label className="mb-1.5">증상</Label>
                  <Textarea
                    placeholder="오늘의 증상을 기록해주세요"
                    value={form.symptoms_text}
                    onChange={(e) => setForm({ ...form, symptoms_text: e.target.value })}
                    className="min-h-20"
                  />
                </div>

                <div>
                  <Label className="mb-1.5">메모 (선택)</Label>
                  <Textarea
                    placeholder="추가 메모"
                    value={form.notes}
                    onChange={(e) => setForm({ ...form, notes: e.target.value })}
                    className="min-h-16"
                  />
                </div>
              </div>

              <div className="flex gap-2 mt-6">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => setShowModal(false)}
                >
                  취소
                </Button>
                <Button
                  className="flex-1 bg-blue-700 hover:bg-blue-800"
                  onClick={handleCreate}
                  disabled={submitting}
                >
                  {submitting ? "저장 중…" : "저장"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}