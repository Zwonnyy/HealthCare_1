"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import Navbar from "@/components/Navbar";
import PaginationBar from "@/components/PaginationBar";
import {
  appointmentApi, userApi,
  Appointment, AppointmentStatus, DoctorSearchResult, PaginatedResponse,
} from "@/lib/api";
import { getToken, getUser } from "@/lib/auth";

const STATUS_CONFIG: Record<AppointmentStatus, { label: string; color: string }> = {
  PENDING:   { label: "대기 중",  color: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400" },
  CONFIRMED: { label: "확정됨",   color: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" },
  CANCELLED: { label: "취소됨",   color: "bg-zinc-100 text-zinc-500 dark:bg-zinc-700 dark:text-zinc-400" },
  COMPLETED: { label: "완료",     color: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" },
};

export default function AppointmentsPage() {
  const router = useRouter();
  const user = getUser();

  const [data, setData] = useState<PaginatedResponse<Appointment> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [showCreate, setShowCreate] = useState(false);
  const [doctorQuery, setDoctorQuery] = useState("");
  const [doctorResults, setDoctorResults] = useState<DoctorSearchResult[]>([]);
  const [selectedDoctor, setSelectedDoctor] = useState<DoctorSearchResult | null>(null);
  const [requestedAt, setRequestedAt] = useState("");
  const [patientNotes, setPatientNotes] = useState("");
  const [creating, setCreating] = useState(false);

  const [actionAppt, setActionAppt] = useState<Appointment | null>(null);
  const [doctorNotes, setDoctorNotes] = useState("");
  const [updating, setUpdating] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    appointmentApi.list(page, 10)
      .then(({ data: res }) => setData(res))
      .catch(() => toast.error("예약 목록을 불러오지 못했어요."))
      .finally(() => setLoading(false));
  }, [page]);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    load();
  }, [router, load]);

  useEffect(() => {
    if (!doctorQuery || user?.role !== "PATIENT") { setDoctorResults([]); return; }
    const t = setTimeout(() => {
      userApi.searchDoctors(doctorQuery).then(({ data: d }) => setDoctorResults(d)).catch(() => {});
    }, 300);
    return () => clearTimeout(t);
  }, [doctorQuery, user?.role]);

  async function handleCreate() {
    if (!selectedDoctor) { toast.error("의사를 선택해주세요."); return; }
    if (!requestedAt) { toast.error("예약 날짜를 입력해주세요."); return; }
    setCreating(true);
    try {
      await appointmentApi.create({
        doctor_id: selectedDoctor.id,
        requested_at: new Date(requestedAt).toISOString(),
        patient_notes: patientNotes || undefined,
      });
      toast.success("예약을 요청했어요.");
      setShowCreate(false);
      setSelectedDoctor(null); setDoctorQuery(""); setRequestedAt(""); setPatientNotes("");
      load();
    } catch {
      toast.error("예약 요청에 실패했어요.");
    } finally {
      setCreating(false);
    }
  }

  async function handleUpdate(status: AppointmentStatus) {
    if (!actionAppt) return;
    setUpdating(true);
    try {
      await appointmentApi.updateStatus(actionAppt.id, { status, doctor_notes: doctorNotes || undefined });
      toast.success("예약 상태를 업데이트했어요.");
      setActionAppt(null); setDoctorNotes("");
      load();
    } catch {
      toast.error("업데이트에 실패했어요.");
    } finally {
      setUpdating(false);
    }
  }

  async function handleCancel(id: number) {
    if (!confirm("예약을 취소할까요?")) return;
    try {
      await appointmentApi.cancel(id);
      toast.success("예약을 취소했어요.");
      load();
    } catch {
      toast.error("취소에 실패했어요.");
    }
  }

  function fmt(iso: string) {
    return new Date(iso).toLocaleDateString("ko-KR", {
      year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
  }

  const appointments = data?.items ?? [];

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">예약</h1>
            <p className="text-sm text-zinc-500 mt-1">
              {user?.role === "PATIENT" ? "의사 예약을 요청하고 관리하세요." : "환자 예약 요청을 확인하고 처리하세요."}
            </p>
          </div>
          {user?.role === "PATIENT" && (
            <Button onClick={() => setShowCreate(true)} className="bg-blue-700 hover:bg-blue-800">
              + 예약 요청
            </Button>
          )}
        </div>

        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="h-24 rounded-xl bg-zinc-200 dark:bg-zinc-800 animate-pulse" />)}
          </div>
        )}

        {!loading && appointments.length === 0 && (
          <div className="text-center py-20 text-zinc-400">
            <p className="text-5xl mb-4">📅</p>
            <p className="text-lg font-medium">예약이 없어요</p>
          </div>
        )}

        <div className="space-y-3">
          {appointments.map((appt) => {
            const sc = STATUS_CONFIG[appt.status];
            return (
              <div key={appt.id} className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 rounded-xl p-5">
                <div className="flex items-start justify-between">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${sc.color}`}>{sc.label}</span>
                      <span className="text-sm font-medium text-zinc-800 dark:text-zinc-200">{fmt(appt.requested_at)}</span>
                    </div>
                    <p className="text-xs text-zinc-400">
                      {user?.role === "PATIENT" ? `의사 #${appt.doctor_id}` : `환자 #${appt.patient_id}`}
                    </p>
                    {appt.patient_notes && (
                      <p className="text-sm text-zinc-600 dark:text-zinc-400">{appt.patient_notes}</p>
                    )}
                    {appt.doctor_notes && (
                      <p className="text-sm text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/10 rounded px-2 py-1">
                        의사 메모: {appt.doctor_notes}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col gap-1 ml-4">
                    {user?.role === "DOCTOR" && appt.status === "PENDING" && (
                      <Button size="sm" className="bg-blue-700 hover:bg-blue-800 h-7 text-xs" onClick={() => { setActionAppt(appt); setDoctorNotes(""); }}>
                        처리
                      </Button>
                    )}
                    {user?.role === "PATIENT" && (appt.status === "PENDING" || appt.status === "CONFIRMED") && (
                      <Button size="sm" variant="outline" className="h-7 text-xs text-red-500 border-red-200" onClick={() => handleCancel(appt.id)}>
                        취소
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {data && <PaginationBar page={data.page} pages={data.pages} onPageChange={setPage} />}

        {/* 예약 요청 모달 (환자) */}
        {showCreate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white dark:bg-zinc-800 rounded-2xl shadow-xl w-full max-w-md p-6">
              <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 mb-4">예약 요청</h2>
              <div className="space-y-4">
                <div>
                  <Label className="mb-1.5">의사 검색</Label>
                  <Input
                    placeholder="의사 이름 또는 이메일"
                    value={doctorQuery}
                    onChange={(e) => { setDoctorQuery(e.target.value); setSelectedDoctor(null); }}
                    className="dark:bg-zinc-700 dark:border-zinc-600"
                  />
                  {doctorResults.length > 0 && !selectedDoctor && (
                    <ul className="mt-1 border border-zinc-200 dark:border-zinc-600 rounded-lg overflow-hidden">
                      {doctorResults.map((d) => (
                        <li key={d.id}>
                          <button
                            className="w-full text-left px-3 py-2 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300"
                            onClick={() => { setSelectedDoctor(d); setDoctorQuery(d.name); setDoctorResults([]); }}
                          >
                            {d.name} <span className="text-zinc-400 text-xs">({d.email})</span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                  {selectedDoctor && <p className="text-xs text-blue-600 mt-1">선택됨: {selectedDoctor.name}</p>}
                </div>
                <div>
                  <Label className="mb-1.5">희망 날짜/시간</Label>
                  <Input type="datetime-local" value={requestedAt} onChange={(e) => setRequestedAt(e.target.value)} className="dark:bg-zinc-700 dark:border-zinc-600" />
                </div>
                <div>
                  <Label className="mb-1.5">메모 (선택)</Label>
                  <Textarea placeholder="증상이나 방문 이유를 적어주세요" value={patientNotes} onChange={(e) => setPatientNotes(e.target.value)} className="min-h-20 dark:bg-zinc-700 dark:border-zinc-600" />
                </div>
              </div>
              <div className="flex gap-2 mt-6">
                <Button variant="outline" className="flex-1" onClick={() => setShowCreate(false)}>취소</Button>
                <Button className="flex-1 bg-blue-700 hover:bg-blue-800" onClick={handleCreate} disabled={creating}>
                  {creating ? "요청 중…" : "예약 요청"}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* 예약 처리 모달 (의사) */}
        {actionAppt && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white dark:bg-zinc-800 rounded-2xl shadow-xl w-full max-w-md p-6">
              <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 mb-2">예약 처리</h2>
              <p className="text-sm text-zinc-500 mb-4">환자 #{actionAppt.patient_id} — {fmt(actionAppt.requested_at)}</p>
              {actionAppt.patient_notes && (
                <p className="text-sm text-zinc-600 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-700 rounded p-3 mb-4">{actionAppt.patient_notes}</p>
              )}
              <div className="mb-4">
                <Label className="mb-1.5">의사 메모 (선택)</Label>
                <Textarea placeholder="환자에게 전달할 메시지" value={doctorNotes} onChange={(e) => setDoctorNotes(e.target.value)} className="min-h-16 dark:bg-zinc-700 dark:border-zinc-600" />
              </div>
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1" onClick={() => setActionAppt(null)}>닫기</Button>
                <Button variant="outline" className="flex-1 text-red-500 border-red-200" onClick={() => handleUpdate("CANCELLED")} disabled={updating}>취소 처리</Button>
                <Button className="flex-1 bg-blue-700 hover:bg-blue-800" onClick={() => handleUpdate("CONFIRMED")} disabled={updating}>
                  {updating ? "처리 중…" : "확정"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
