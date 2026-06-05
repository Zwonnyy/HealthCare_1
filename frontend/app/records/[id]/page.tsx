"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import Navbar from "@/components/Navbar";
import {
  recordApi,
  medicationCheckApi,
  drugInteractionApi,
  MedicalRecord,
  Guide,
  TodayMedication,
  DrugInteraction,
  ActionPlan,
} from "@/lib/api";
import { getToken, getUser } from "@/lib/auth";

const statusConfig: Record<string, { label: string; color: string; icon: string }> = {
  PENDING:    { label: "대기 중",    color: "bg-zinc-100 text-zinc-500",       icon: "⏳" },
  GENERATING: { label: "생성 중...", color: "bg-amber-50 text-amber-600",       icon: "✨" },
  COMPLETED:  { label: "완료",       color: "bg-emerald-50 text-emerald-600",   icon: "✅" },
  FAILED:     { label: "실패",       color: "bg-red-50 text-red-500",           icon: "❌" },
};

export default function RecordDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [user, setUser] = useState<ReturnType<typeof getUser>>(null);
  const [record, setRecord] = useState<MedicalRecord | null>(null);
  const [actionPlan, setActionPlan] = useState<ActionPlan | null>(null);
  const [guides, setGuides] = useState<Guide[]>([]);
  const [requesting, setRequesting] = useState(false);

  const [showEdit, setShowEdit] = useState(false);
  const [editForm, setEditForm] = useState({ diagnosis: "", symptoms: "", notes: "" });
  const [saving, setSaving] = useState(false);

  const [todayMeds, setTodayMeds] = useState<TodayMedication[]>([]);
  const [togglingId, setTogglingId] = useState<number | null>(null);

  const [interaction, setInteraction] = useState<DrugInteraction | null>(null);
  const [checkingInteraction, setCheckingInteraction] = useState(false);

  const loadGuides = useCallback(() => {
    recordApi.getGuides(Number(id)).then(({ data }) => setGuides(data));
  }, [id]);

  useEffect(() => {
    const u = getUser();
    setUser(u);
    if (!getToken()) { router.push("/login"); return; }
    recordApi.get(Number(id))
      .then(({ data }) => {
        setRecord(data);
        setEditForm({ diagnosis: data.diagnosis, symptoms: data.symptoms, notes: data.notes ?? "" });
      })
      .catch(() => { toast.error("기록을 찾을 수 없어요."); router.push("/records"); });
    loadGuides();
    recordApi.actionPlan(Number(id)).then(({ data }) => setActionPlan(data)).catch(() => {});
    if (getUser()?.role === "PATIENT") {
      medicationCheckApi.today().then(({ data }) => setTodayMeds(data)).catch(() => {});
    }
    drugInteractionApi.getLatest(Number(id)).then(({ data }) => setInteraction(data)).catch(() => {});
  }, [id, router, loadGuides]);

  useEffect(() => {
    const hasActive = guides.some((g) => g.status === "PENDING" || g.status === "GENERATING");
    if (!hasActive) return;
    const t = setTimeout(loadGuides, 3000);
    return () => clearTimeout(t);
  }, [guides, loadGuides]);

  async function requestGuide() {
    setRequesting(true);
    try {
      await recordApi.requestGuide(Number(id));
      toast.success("AI 가이드 생성을 요청했어요.");
      loadGuides();
    } catch {
      toast.error("요청에 실패했어요.");
    } finally {
      setRequesting(false);
    }
  }

  async function handleToggleMed(prescriptionId: number) {
    setTogglingId(prescriptionId);
    try {
      const { data } = await medicationCheckApi.toggle(prescriptionId);
      setTodayMeds((prev) =>
        prev.map((m) => m.prescription.id === prescriptionId ? { ...m, checked: data.checked } : m)
      );
    } catch {
      toast.error("체크 처리에 실패했어요.");
    } finally {
      setTogglingId(null);
    }
  }

  async function handleCheckInteraction() {
    setCheckingInteraction(true);
    try {
      const { data } = await drugInteractionApi.check(Number(id));
      setInteraction(data);
      if (data.has_warning) toast.warning("⚠️ 약물 상호작용 경고가 있어요. 결과를 확인하세요.");
      else toast.success("약물 상호작용 분석이 완료됐어요.");
    } catch {
      toast.error("분석 요청에 실패했어요.");
    } finally {
      setCheckingInteraction(false);
    }
  }

  async function handleSaveEdit() {
    setSaving(true);
    try {
      const updated = await recordApi.update(Number(id), {
        diagnosis: editForm.diagnosis.trim() || undefined,
        symptoms: editForm.symptoms.trim() || undefined,
        notes: editForm.notes.trim() || undefined,
      });
      setRecord(updated.data);
      setShowEdit(false);
      toast.success("진료 기록을 수정했어요.");
    } catch {
      toast.error("수정에 실패했어요.");
    } finally {
      setSaving(false);
    }
  }

  if (!record) {
    return (
      <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
        <Navbar />
        <div className="max-w-3xl mx-auto px-4 py-16 space-y-3">
          {[1, 2, 3].map((i) => <div key={i} className="h-20 rounded-xl bg-zinc-200 dark:bg-zinc-800 animate-pulse" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-10 space-y-6">

        <div className="flex items-center justify-between">
          <Link href="/records" className="inline-flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 transition-colors">
            ← 진료 기록 목록
          </Link>
          <button
            onClick={() => window.print()}
            className="text-xs text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 flex items-center gap-1 transition-colors"
          >
            🖨️ PDF 출력
          </button>
        </div>

        <div className="bg-white dark:bg-zinc-800 rounded-2xl border border-zinc-100 dark:border-zinc-700 shadow-sm overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-blue-500 px-6 py-5 text-white">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-blue-100 text-xs mb-1">진단명</p>
                <h1 className="text-2xl font-bold">{record.diagnosis}</h1>
              </div>
              <div className="flex items-center gap-2">
                {user?.role === "DOCTOR" && (
                  <button
                    onClick={() => setShowEdit(true)}
                    className="text-xs bg-white/20 hover:bg-white/30 px-3 py-1 rounded-lg transition-colors"
                  >
                    ✏️ 수정
                  </button>
                )}
                <Badge className="bg-white/20 text-white border-0 text-xs">
                  {new Date(record.visited_at).toLocaleDateString("ko-KR", { year: "numeric", month: "long", day: "numeric" })}
                </Badge>
              </div>
            </div>
          </div>

          <div className="p-6 space-y-5">
            <div>
              <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wide mb-2">주요 증상</p>
              <p className="text-zinc-700 dark:text-zinc-300">{record.symptoms}</p>
            </div>
            {record.notes && (
              <div>
                <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wide mb-2">의사 메모</p>
                <p className="text-zinc-700 dark:text-zinc-300 bg-zinc-50 dark:bg-zinc-700 rounded-lg p-3 text-sm">{record.notes}</p>
              </div>
            )}

            <div>
              <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wide mb-3">처방 약물</p>
              <div className="grid gap-2">
                {record.prescriptions.map((p) => (
                  <div key={p.id} className="flex items-center justify-between rounded-lg border border-zinc-100 dark:border-zinc-700 px-4 py-3">
                    <div>
                      <span className="font-medium text-zinc-800 dark:text-zinc-200">{p.medication_name}</span>
                      <span className="ml-2 text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded-full">{p.dosage}</span>
                    </div>
                    <div className="text-right text-xs text-zinc-400">
                      <p>{p.frequency}</p>
                      <p>{p.duration_days}일</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {actionPlan && (
          <div className="bg-white dark:bg-zinc-800 rounded-2xl border border-zinc-100 dark:border-zinc-700 shadow-sm p-6">
            <div className="flex items-start justify-between gap-3 mb-5">
              <div>
                <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">{actionPlan.title}</h2>
                <p className="text-xs text-zinc-400 mt-1">{actionPlan.summary}</p>
              </div>
              <span className="rounded-full bg-blue-50 dark:bg-blue-900/30 px-3 py-1 text-xs font-semibold text-blue-700 dark:text-blue-300">
                {actionPlan.items.length}개 할 일
              </span>
            </div>
            <div className="space-y-3">
              {actionPlan.items.map((item) => (
                <article key={`${item.category}-${item.title}`} className="rounded-lg border border-zinc-100 dark:border-zinc-700 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-zinc-100 dark:bg-zinc-700 px-2 py-0.5 text-xs font-semibold text-zinc-600 dark:text-zinc-300">
                        {item.category}
                      </span>
                      <p className="font-semibold text-zinc-900 dark:text-zinc-100">{item.title}</p>
                    </div>
                    <div className="flex gap-2 text-xs">
                      <span className="text-zinc-400">{item.due_label}</span>
                      <span className={item.priority === "높음" ? "text-red-500 font-semibold" : "text-amber-500 font-semibold"}>
                        {item.priority}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-zinc-600 dark:text-zinc-300">{item.detail}</p>
                </article>
              ))}
            </div>
          </div>
        )}

        {user?.role === "PATIENT" && todayMeds.length > 0 && (
          <div className="bg-white dark:bg-zinc-800 rounded-2xl border border-zinc-100 dark:border-zinc-700 shadow-sm p-6">
            <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 mb-1">오늘의 복약 체크</h2>
            <p className="text-xs text-zinc-400 mb-4">복용한 약에 체크하세요.</p>
            <div className="space-y-2">
              {todayMeds.map((item) => (
                <button
                  key={item.prescription.id}
                  onClick={() => handleToggleMed(item.prescription.id)}
                  disabled={togglingId === item.prescription.id}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg border transition-all text-left ${
                    item.checked
                      ? "border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/10"
                      : "border-zinc-100 dark:border-zinc-700 hover:border-zinc-200 dark:hover:border-zinc-600"
                  }`}
                >
                  <span className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors ${
                    item.checked ? "border-emerald-500 bg-emerald-500" : "border-zinc-300 dark:border-zinc-600"
                  }`}>
                    {item.checked && <span className="text-white text-xs">✓</span>}
                  </span>
                  <div className="flex-1 min-w-0">
                    <span className={`font-medium text-sm ${item.checked ? "line-through text-zinc-400" : "text-zinc-800 dark:text-zinc-200"}`}>
                      {item.prescription.medication_name}
                    </span>
                    <span className="ml-2 text-xs text-zinc-400">{item.prescription.dosage} · {item.prescription.frequency}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="bg-white dark:bg-zinc-800 rounded-2xl border border-zinc-100 dark:border-zinc-700 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">약물 상호작용 분석</h2>
              <p className="text-xs text-zinc-400 mt-0.5">AI가 처방 약물 간 위험한 상호작용을 분석해요.</p>
            </div>
            <Button
              onClick={handleCheckInteraction}
              disabled={checkingInteraction}
              size="sm"
              variant="outline"
              className="border-amber-300 text-amber-700 hover:bg-amber-50 dark:border-amber-700 dark:text-amber-400 dark:hover:bg-amber-900/20"
            >
              {checkingInteraction ? "분석 중..." : "⚡ 상호작용 검사"}
            </Button>
          </div>

          {!interaction ? (
            <div className="text-center py-8 text-zinc-400">
              <p className="text-3xl mb-2">💊</p>
              <p className="text-sm">위 버튼을 눌러 약물 상호작용을 분석하세요.</p>
            </div>
          ) : interaction.status === "FAILED" ? (
            <div className="rounded-xl border border-red-100 dark:border-red-900 bg-red-50 dark:bg-red-900/10 p-4 text-sm text-red-600 dark:text-red-400">
              분석에 실패했어요. 다시 시도해주세요.
            </div>
          ) : (
            <div className={`rounded-xl border p-4 ${
              interaction.has_warning
                ? "border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/10"
                : "border-emerald-100 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/10"
            }`}>
              <p className={`text-xs font-semibold mb-2 ${interaction.has_warning ? "text-amber-700 dark:text-amber-400" : "text-emerald-700 dark:text-emerald-400"}`}>
                {interaction.has_warning ? "⚠️ 주의사항이 있습니다" : "✅ 주요 상호작용 없음"}
              </p>
              <p className="text-sm text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap leading-relaxed">
                {interaction.result_text}
              </p>
              <p className="text-xs text-zinc-400 mt-3">
                분석 시각: {new Date(interaction.created_at).toLocaleString("ko-KR")}
              </p>
            </div>
          )}
        </div>

        <div className="bg-white dark:bg-zinc-800 rounded-2xl border border-zinc-100 dark:border-zinc-700 shadow-sm p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">AI 복약 가이드</h2>
              <p className="text-xs text-zinc-400 mt-0.5">AI가 생성하는 맞춤 복약 안내</p>
            </div>
            {user?.role === "PATIENT" && (
              <Button
                onClick={requestGuide}
                disabled={requesting}
                size="sm"
                className="bg-blue-700 hover:bg-blue-800"
              >
                {requesting ? "요청 중..." : "✨ 가이드 생성"}
              </Button>
            )}
          </div>

          {guides.length === 0 ? (
            <div className="text-center py-10 text-zinc-400">
              <p className="text-3xl mb-3">🤖</p>
              <p className="text-sm">
                {user?.role === "PATIENT"
                  ? "위 버튼을 눌러 AI 가이드를 생성해보세요."
                  : "환자가 아직 가이드를 요청하지 않았어요."}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {guides.map((g) => {
                const s = statusConfig[g.status];
                return (
                  <div key={g.id} className={`rounded-xl border px-4 py-4 flex items-center justify-between ${
                    g.status === "GENERATING" ? "border-amber-200 bg-amber-50/50 dark:bg-amber-900/10" :
                    g.status === "COMPLETED"  ? "border-emerald-100 dark:border-emerald-800" : "border-zinc-100 dark:border-zinc-700"
                  }`}>
                    <div className="flex items-center gap-3">
                      <span className="text-xl">{s.icon}</span>
                      <div>
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${s.color}`}>
                          {s.label}
                        </span>
                        <p className="text-xs text-zinc-400 mt-1">
                          {new Date(g.created_at).toLocaleString("ko-KR")}
                        </p>
                      </div>
                    </div>
                    {g.status === "COMPLETED" && (
                      <Link href={`/guides/${g.id}`}>
                        <Button size="sm" variant="outline" className="text-blue-600 border-blue-200 hover:bg-blue-50">
                          가이드 보기 →
                        </Button>
                      </Link>
                    )}
                    {(g.status === "PENDING" || g.status === "GENERATING") && (
                      <span className="text-xs text-zinc-400 animate-pulse">자동 갱신 중</span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>

      {showEdit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-zinc-800 rounded-2xl shadow-xl w-full max-w-lg p-6">
            <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 mb-4">진료 기록 수정</h2>
            <div className="space-y-4">
              <div>
                <Label className="mb-1.5">진단명</Label>
                <Input
                  value={editForm.diagnosis}
                  onChange={(e) => setEditForm({ ...editForm, diagnosis: e.target.value })}
                  className="dark:bg-zinc-700 dark:border-zinc-600"
                />
              </div>
              <div>
                <Label className="mb-1.5">주요 증상</Label>
                <Textarea
                  value={editForm.symptoms}
                  onChange={(e) => setEditForm({ ...editForm, symptoms: e.target.value })}
                  className="min-h-20 dark:bg-zinc-700 dark:border-zinc-600"
                />
              </div>
              <div>
                <Label className="mb-1.5">의사 메모 (선택)</Label>
                <Textarea
                  value={editForm.notes}
                  onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                  className="min-h-16 dark:bg-zinc-700 dark:border-zinc-600"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <Button variant="outline" className="flex-1" onClick={() => setShowEdit(false)}>
                취소
              </Button>
              <Button className="flex-1 bg-blue-700 hover:bg-blue-800" onClick={handleSaveEdit} disabled={saving}>
                {saving ? "저장 중…" : "저장"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
