"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  appointmentApi,
  healthInsightApi,
  userApi,
  type Appointment,
  type ClinicalNoteDraft,
  type HealthRisk,
  type MedicationAdherence,
  type MedicationPattern,
  type PatientSearchResult,
  type PatientTimeline,
  type PreVisitQuestionnaire,
} from "@/lib/api";
import { getToken, getUser } from "@/lib/auth";

const riskColor: Record<string, string> = {
  낮음: "text-emerald-600 bg-emerald-50 border-emerald-100",
  주의: "text-amber-600 bg-amber-50 border-amber-100",
  높음: "text-red-600 bg-red-50 border-red-100",
};

const timelineTypeLabel: Record<string, string> = {
  record: "진료",
  health_log: "일지",
  vital: "바이탈",
  symptom_check: "증상",
  pre_visit: "문진",
};

export default function HealthInsightsPage() {
  const router = useRouter();
  const user = getUser();
  const [risk, setRisk] = useState<HealthRisk | null>(null);
  const [adherence, setAdherence] = useState<MedicationAdherence | null>(null);
  const [medicationPattern, setMedicationPattern] = useState<MedicationPattern | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [preVisits, setPreVisits] = useState<PreVisitQuestionnaire[]>([]);
  const [patientQuery, setPatientQuery] = useState("");
  const [patientResults, setPatientResults] = useState<PatientSearchResult[]>([]);
  const [timeline, setTimeline] = useState<PatientTimeline | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [drafts, setDrafts] = useState<Record<number, ClinicalNoteDraft>>({});
  const [draftingId, setDraftingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    appointment_id: "",
    symptoms: "",
    onset: "",
    severity: "5",
    medications: "",
    history: "",
    questions: "",
  });

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    const requests =
      user?.role === "PATIENT"
        ? [
            healthInsightApi.risk(),
            healthInsightApi.medicationAdherence(),
            healthInsightApi.medicationPatterns(),
            appointmentApi.list(1, 50),
            healthInsightApi.preVisits(),
          ]
        : [healthInsightApi.preVisits()];

    Promise.all(requests)
      .then((responses) => {
        if (user?.role === "PATIENT") {
          setRisk(responses[0].data as HealthRisk);
          setAdherence(responses[1].data as MedicationAdherence);
          setMedicationPattern(responses[2].data as MedicationPattern);
          setAppointments((responses[3].data as { items: Appointment[] }).items);
          setPreVisits(responses[4].data as PreVisitQuestionnaire[]);
        } else {
          setPreVisits(responses[0].data as PreVisitQuestionnaire[]);
        }
      })
      .catch(() => toast.error("AI 인사이트 데이터를 불러오지 못했어요."))
      .finally(() => setLoading(false));
  }, [router, user?.role]);

  async function handlePatientSearch() {
    if (!patientQuery.trim()) {
      toast.error("환자 이름이나 이메일을 입력해주세요.");
      return;
    }
    try {
      const { data } = await userApi.searchPatients(patientQuery.trim());
      setPatientResults(data);
      if (data.length === 0) toast.info("검색된 환자가 없습니다.");
    } catch {
      toast.error("환자 검색에 실패했어요.");
    }
  }

  async function loadTimeline(patient: PatientSearchResult) {
    setTimelineLoading(true);
    try {
      const { data } = await healthInsightApi.patientTimeline(patient.id);
      setTimeline(data);
    } catch {
      toast.error("환자 타임라인을 불러오지 못했어요.");
    } finally {
      setTimelineLoading(false);
    }
  }

  async function handleCreateDraft(preVisitId: number) {
    setDraftingId(preVisitId);
    try {
      const { data } = await healthInsightApi.clinicalNoteDraft(preVisitId);
      setDrafts((prev) => ({ ...prev, [preVisitId]: data }));
      toast.success("진료 메모 초안을 생성했어요.");
    } catch {
      toast.error("진료 메모 초안 생성에 실패했어요.");
    } finally {
      setDraftingId(null);
    }
  }

  async function handleCreatePreVisit() {
    if (!form.appointment_id) {
      toast.error("예약을 선택해주세요.");
      return;
    }
    if (!form.symptoms.trim()) {
      toast.error("주요 증상을 입력해주세요.");
      return;
    }
    setCreating(true);
    try {
      const { data } = await healthInsightApi.createPreVisit(Number(form.appointment_id), {
        symptoms: form.symptoms.trim(),
        onset: form.onset.trim() || undefined,
        severity: Number(form.severity),
        medications: form.medications.trim() || undefined,
        history: form.history.trim() || undefined,
        questions: form.questions.trim() || undefined,
      });
      setPreVisits((prev) => [data, ...prev]);
      setForm({ appointment_id: "", symptoms: "", onset: "", severity: "5", medications: "", history: "", questions: "" });
      toast.success("진료 전 문진 요약을 생성했어요.");
    } catch {
      toast.error("문진 저장에 실패했어요.");
    } finally {
      setCreating(false);
    }
  }

  const pendingAppointments = appointments.filter((appointment) => appointment.status !== "CANCELLED");

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            {user?.role === "DOCTOR" ? "진료 전 문진 요약" : "AI 건강 인사이트"}
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            {user?.role === "DOCTOR"
              ? "예약 전 환자가 작성한 문진과 AI 요약을 확인합니다."
              : "건강 리스크, 복약 순응도, 진료 전 문진을 한 화면에서 관리합니다."}
          </p>
        </div>

        {loading && <div className="h-48 rounded-lg bg-zinc-200 dark:bg-zinc-800 animate-pulse" />}

        {!loading && user?.role === "DOCTOR" && (
          <section className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 rounded-lg p-5 mb-8">
            <div className="flex flex-col md:flex-row md:items-end gap-3">
              <div className="flex-1">
                <Label>환자 검색</Label>
                <Input
                  value={patientQuery}
                  onChange={(e) => setPatientQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handlePatientSearch();
                  }}
                  placeholder="환자 이름 또는 이메일"
                  className="mt-2"
                />
              </div>
              <Button onClick={handlePatientSearch} className="bg-blue-700 hover:bg-blue-800">
                검색
              </Button>
            </div>

            {patientResults.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {patientResults.map((patient) => (
                  <button
                    key={patient.id}
                    type="button"
                    onClick={() => loadTimeline(patient)}
                    className="rounded-md border border-zinc-200 dark:border-zinc-700 px-3 py-2 text-left text-sm hover:bg-zinc-50 dark:hover:bg-zinc-900"
                  >
                    <span className="font-medium text-zinc-900 dark:text-zinc-100">{patient.name}</span>
                    <span className="ml-2 text-zinc-400">{patient.email}</span>
                  </button>
                ))}
              </div>
            )}
          </section>
        )}

        {!loading && user?.role === "DOCTOR" && (
          <section className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 rounded-lg p-5 mb-8">
            <div className="flex items-center justify-between gap-3 mb-4">
              <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">
                {timeline ? `${timeline.patient_name} 타임라인` : "환자 타임라인"}
              </h2>
              {timeline && <span className="text-xs text-zinc-400">최근 {timeline.period_days}일</span>}
            </div>
            {timelineLoading && <div className="h-32 rounded-lg bg-zinc-100 dark:bg-zinc-900 animate-pulse" />}
            {!timelineLoading && !timeline && <p className="text-sm text-zinc-400">환자를 선택하면 진료 흐름을 볼 수 있습니다.</p>}
            {!timelineLoading && timeline?.items.length === 0 && <p className="text-sm text-zinc-400">표시할 타임라인이 없습니다.</p>}
            {!timelineLoading && timeline && timeline.items.length > 0 && (
              <div className="space-y-3">
                {timeline.items.map((item) => (
                  <article key={`${item.type}-${item.id}`} className="rounded-md border border-zinc-100 dark:border-zinc-700 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="rounded-full bg-blue-50 dark:bg-blue-900/30 px-2 py-0.5 text-xs font-semibold text-blue-700 dark:text-blue-300">
                          {timelineTypeLabel[item.type] ?? item.type}
                        </span>
                        <p className="font-medium text-zinc-900 dark:text-zinc-100">{item.title}</p>
                      </div>
                      <p className="text-xs text-zinc-400">{new Date(item.occurred_at).toLocaleString("ko-KR")}</p>
                    </div>
                    <p className="text-sm text-zinc-600 dark:text-zinc-300 whitespace-pre-line">{item.summary}</p>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}

        {!loading && user?.role === "PATIENT" && (
          <div className="grid lg:grid-cols-2 gap-5 mb-8">
            <section className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 rounded-lg p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">건강 리스크 예측</h2>
                {risk && (
                  <span className={`px-3 py-1 rounded-full border text-sm font-semibold ${riskColor[risk.risk_level]}`}>
                    {risk.risk_level} · {risk.score}점
                  </span>
                )}
              </div>
              <p className="text-sm text-zinc-600 dark:text-zinc-300 mb-4">{risk?.summary}</p>
              <div className="space-y-2">
                {(risk?.signals.length ? risk.signals : [{ label: "특이 신호 없음", detail: "최근 데이터 기준 큰 위험 신호가 없습니다.", severity: 0 }]).map((signal) => (
                  <div key={`${signal.label}-${signal.detail}`} className="rounded-md bg-zinc-50 dark:bg-zinc-900 p-3">
                    <p className="text-sm font-medium text-zinc-800 dark:text-zinc-200">{signal.label}</p>
                    <p className="text-xs text-zinc-500 mt-1">{signal.detail}</p>
                  </div>
                ))}
              </div>
              <ul className="mt-4 space-y-1 text-xs text-zinc-500">
                {risk?.recommendations.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </section>

            <section className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 rounded-lg p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">복약 순응도</h2>
                <span className="text-2xl font-bold text-blue-700 dark:text-blue-400">{adherence?.overall_rate ?? 0}%</span>
              </div>
              <p className="text-sm text-zinc-600 dark:text-zinc-300 mb-4">{adherence?.summary}</p>
              <div className="space-y-3">
                {adherence?.items.length === 0 && <p className="text-sm text-zinc-400">분석할 복약 기록이 없습니다.</p>}
                {adherence?.items.map((item) => (
                  <div key={item.prescription_id}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-zinc-700 dark:text-zinc-300">{item.medication_name}</span>
                      <span className="text-zinc-500">{item.checked_days}/{item.expected_days}일</span>
                    </div>
                    <div className="h-2 rounded-full bg-zinc-100 dark:bg-zinc-700">
                      <div className="h-2 rounded-full bg-blue-600" style={{ width: `${Math.min(item.adherence_rate, 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              {medicationPattern && (
                <div className="mt-5 rounded-md bg-zinc-50 dark:bg-zinc-900 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">누락 패턴</p>
                    <span className="text-xs text-zinc-400">
                      연속 누락 {medicationPattern.current_missed_streak}일
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">{medicationPattern.summary}</p>
                  {medicationPattern.weakest_weekdays.length > 0 && (
                    <div className="mt-3 grid grid-cols-3 gap-2">
                      {medicationPattern.weakest_weekdays.map((day) => (
                        <div key={day.weekday} className="rounded-md border border-zinc-200 dark:border-zinc-700 p-2">
                          <p className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">{day.weekday}요일</p>
                          <p className="mt-1 text-lg font-bold text-blue-700 dark:text-blue-300">{day.adherence_rate}%</p>
                          <p className="text-xs text-zinc-400">누락 {day.missed_count}회</p>
                        </div>
                      ))}
                    </div>
                  )}
                  <ul className="mt-3 space-y-1 text-xs text-zinc-500">
                    {medicationPattern.suggestions.map((suggestion) => (
                      <li key={suggestion}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </section>
          </div>
        )}

        {!loading && user?.role === "PATIENT" && (
          <section className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 rounded-lg p-5 mb-8">
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100 mb-4">진료 전 AI 문진 작성</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label>예약 선택</Label>
                <select
                  value={form.appointment_id}
                  onChange={(e) => setForm({ ...form, appointment_id: e.target.value })}
                  className="mt-2 w-full h-10 rounded-md border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 text-sm"
                >
                  <option value="">예약을 선택하세요</option>
                  {pendingAppointments.map((appointment) => (
                    <option key={appointment.id} value={appointment.id}>
                      {new Date(appointment.requested_at).toLocaleString("ko-KR")} · {appointment.status}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>증상 시작 시점</Label>
                <Input value={form.onset} onChange={(e) => setForm({ ...form, onset: e.target.value })} placeholder="예: 3일 전부터" className="mt-2" />
              </div>
              <div>
                <Label>심각도 0-10</Label>
                <Input type="number" min={0} max={10} value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })} className="mt-2" />
              </div>
              <div>
                <Label>복용 중인 약</Label>
                <Input value={form.medications} onChange={(e) => setForm({ ...form, medications: e.target.value })} placeholder="예: 혈압약, 진통제" className="mt-2" />
              </div>
              <div className="md:col-span-2">
                <Label>주요 증상</Label>
                <Textarea value={form.symptoms} onChange={(e) => setForm({ ...form, symptoms: e.target.value })} className="mt-2" rows={3} />
              </div>
              <div>
                <Label>과거 병력</Label>
                <Textarea value={form.history} onChange={(e) => setForm({ ...form, history: e.target.value })} className="mt-2" rows={3} />
              </div>
              <div>
                <Label>의사에게 묻고 싶은 질문</Label>
                <Textarea value={form.questions} onChange={(e) => setForm({ ...form, questions: e.target.value })} className="mt-2" rows={3} />
              </div>
            </div>
            <Button onClick={handleCreatePreVisit} disabled={creating} className="mt-4 bg-blue-700 hover:bg-blue-800">
              {creating ? "생성 중..." : "AI 문진 요약 생성"}
            </Button>
          </section>
        )}

        {!loading && (
          <section className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 rounded-lg p-5">
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100 mb-4">문진 요약 목록</h2>
            <div className="space-y-4">
              {preVisits.length === 0 && <p className="text-sm text-zinc-400">작성된 문진이 없습니다.</p>}
              {preVisits.map((item) => (
                <article key={item.id} className="rounded-md border border-zinc-100 dark:border-zinc-700 p-4">
                  <div className="flex justify-between gap-3 mb-2">
                    <p className="font-medium text-zinc-900 dark:text-zinc-100">예약 #{item.appointment_id}</p>
                    <p className="text-xs text-zinc-400">{new Date(item.created_at).toLocaleString("ko-KR")}</p>
                  </div>
                  <p className="text-sm text-zinc-600 dark:text-zinc-300 whitespace-pre-line">{item.ai_summary}</p>
                  {user?.role === "DOCTOR" && (
                    <div className="mt-4">
                      <Button
                        variant="outline"
                        onClick={() => handleCreateDraft(item.id)}
                        disabled={draftingId === item.id}
                      >
                        {draftingId === item.id ? "생성 중..." : "진료 메모 초안 생성"}
                      </Button>
                      {drafts[item.id] && (
                        <div className="mt-4 rounded-md bg-zinc-50 dark:bg-zinc-900 p-4">
                          <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                            {drafts[item.id].diagnosis_hint}
                          </p>
                          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300 whitespace-pre-line">
                            {drafts[item.id].soap_note}
                          </p>
                          <div className="mt-3">
                            <p className="text-xs font-semibold text-zinc-500">추가 확인 질문</p>
                            <ul className="mt-1 space-y-1 text-xs text-zinc-500">
                              {drafts[item.id].follow_up_questions.map((question) => (
                                <li key={question}>{question}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </article>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
