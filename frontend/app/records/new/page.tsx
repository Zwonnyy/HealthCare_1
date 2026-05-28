"use client";
import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import Navbar from "@/components/Navbar";
import { recordApi, userApi, PatientSearchResult } from "@/lib/api";
import { getErrorMessage } from "@/lib/error";

interface PrescriptionForm {
  medication_name: string;
  dosage: string;
  frequency: string;
  duration_days: number;
  instructions: string;
}

const emptyPrescription = (): PrescriptionForm => ({
  medication_name: "",
  dosage: "",
  frequency: "",
  duration_days: 7,
  instructions: "",
});

export default function NewRecordPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    patient_id: "",
    diagnosis: "",
    symptoms: "",
    notes: "",
    visited_at: new Date().toISOString().slice(0, 16),
  });
  const [prescriptions, setPrescriptions] = useState<PrescriptionForm[]>([emptyPrescription()]);

  // 환자 검색
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<PatientSearchResult[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<PatientSearchResult | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleSearchInput(value: string) {
    setSearchQuery(value);
    setSelectedPatient(null);
    setForm((prev) => ({ ...prev, patient_id: "" }));

    if (searchTimer.current) clearTimeout(searchTimer.current);
    if (!value.trim()) { setSearchResults([]); setShowDropdown(false); return; }

    searchTimer.current = setTimeout(async () => {
      try {
        const { data } = await userApi.searchPatients(value);
        setSearchResults(data);
        setShowDropdown(true);
      } catch {
        setSearchResults([]);
      }
    }, 300);
  }

  function selectPatient(p: PatientSearchResult) {
    setSelectedPatient(p);
    setSearchQuery(p.name);
    setForm((prev) => ({ ...prev, patient_id: String(p.id) }));
    setShowDropdown(false);
  }

  function setField(key: string, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function setPrescField(idx: number, key: string, value: string | number) {
    setPrescriptions((prev) =>
      prev.map((p, i) => (i === idx ? { ...p, [key]: value } : p))
    );
  }

  function addPrescription() {
    setPrescriptions((prev) => [...prev, emptyPrescription()]);
  }

  function removePrescription(idx: number) {
    setPrescriptions((prev) => prev.filter((_, i) => i !== idx));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.patient_id) {
      toast.error("환자를 선택해주세요.");
      return;
    }
    setLoading(true);
    try {
      const { data } = await recordApi.create({
        patient_id: Number(form.patient_id),
        diagnosis: form.diagnosis,
        symptoms: form.symptoms,
        notes: form.notes || undefined,
        visited_at: new Date(form.visited_at).toISOString(),
        prescriptions: prescriptions.map((p) => ({
          ...p,
          instructions: p.instructions || null,
        })),
      });
      toast.success("진료 기록이 등록됐어요.");
      router.push(`/records/${data.id}`);
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, "등록에 실패했어요."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-10 space-y-6">

        <Link href="/records" className="inline-flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-800 transition-colors">
          ← 진료 기록 목록
        </Link>

        {/* 헤더 */}
        <div className="rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
          <p className="text-blue-100 text-sm mb-1">진료 기록 등록</p>
          <h1 className="text-2xl font-bold">새 진료 기록 작성</h1>
          <p className="text-blue-200 text-xs mt-2">환자 정보, 진단명, 처방 약물을 입력하세요.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">

          {/* 기본 정보 */}
          <div className="bg-white rounded-2xl border border-zinc-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-zinc-50 flex items-center gap-2">
              <span className="text-xl">🩺</span>
              <h2 className="font-bold text-zinc-900">기본 정보</h2>
            </div>
            <div className="px-6 py-5 space-y-4">

              {/* 환자 검색 */}
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-zinc-500 uppercase tracking-wide">환자 검색</Label>
                <div className="relative" ref={dropdownRef}>
                  <div className="relative">
                    <Input
                      placeholder="이름 또는 이메일로 검색"
                      value={searchQuery}
                      onChange={(e) => handleSearchInput(e.target.value)}
                      className={`h-10 pr-10 ${selectedPatient ? "border-emerald-300 bg-emerald-50/30" : ""}`}
                      autoComplete="off"
                    />
                    {selectedPatient && (
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-500 text-sm">✓</span>
                    )}
                  </div>

                  {/* 검색 결과 드롭다운 */}
                  {showDropdown && (
                    <div className="absolute z-10 w-full mt-1 bg-white border border-zinc-200 rounded-xl shadow-lg overflow-hidden">
                      {searchResults.length === 0 ? (
                        <div className="px-4 py-3 text-sm text-zinc-400 text-center">검색 결과가 없어요</div>
                      ) : (
                        searchResults.map((p) => (
                          <button
                            key={p.id}
                            type="button"
                            onClick={() => selectPatient(p)}
                            className="w-full px-4 py-3 text-left hover:bg-blue-50 transition-colors flex items-center justify-between border-b border-zinc-50 last:border-0"
                          >
                            <div>
                              <span className="font-medium text-zinc-800 text-sm">{p.name}</span>
                              <span className="ml-2 text-xs text-zinc-400">{p.email}</span>
                            </div>
                            <span className="text-xs text-zinc-300">ID: {p.id}</span>
                          </button>
                        ))
                      )}
                    </div>
                  )}
                </div>

                {selectedPatient && (
                  <div className="flex items-center gap-2 mt-1.5 px-3 py-2 bg-emerald-50 border border-emerald-100 rounded-lg">
                    <span className="text-emerald-500 text-sm">👤</span>
                    <span className="text-sm text-emerald-700 font-medium">{selectedPatient.name}</span>
                    <span className="text-xs text-emerald-500">{selectedPatient.email}</span>
                    <button
                      type="button"
                      onClick={() => { setSelectedPatient(null); setSearchQuery(""); setForm((p) => ({ ...p, patient_id: "" })); }}
                      className="ml-auto text-xs text-emerald-400 hover:text-red-500 transition-colors"
                    >
                      변경
                    </button>
                  </div>
                )}
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-zinc-500 uppercase tracking-wide">진료 일시</Label>
                <Input
                  type="datetime-local"
                  value={form.visited_at}
                  onChange={(e) => setField("visited_at", e.target.value)}
                  className="h-10"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-zinc-500 uppercase tracking-wide">진단명</Label>
                <Input
                  placeholder="예: 고혈압, 당뇨병 2형"
                  value={form.diagnosis}
                  onChange={(e) => setField("diagnosis", e.target.value)}
                  className="h-10"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-zinc-500 uppercase tracking-wide">주요 증상</Label>
                <Textarea
                  placeholder="예: 두통, 어지러움, 피로감, 혈압 상승"
                  value={form.symptoms}
                  onChange={(e) => setField("symptoms", e.target.value)}
                  className="resize-none"
                  rows={3}
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-zinc-500 uppercase tracking-wide">
                  의사 메모 <span className="text-zinc-300 font-normal normal-case">(선택)</span>
                </Label>
                <Textarea
                  placeholder="특이사항, 추가 지시사항 등"
                  value={form.notes}
                  onChange={(e) => setField("notes", e.target.value)}
                  className="resize-none"
                  rows={2}
                />
              </div>
            </div>
          </div>

          {/* 처방 약물 */}
          <div className="bg-white rounded-2xl border border-zinc-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-zinc-50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">💊</span>
                <h2 className="font-bold text-zinc-900">처방 약물</h2>
                <span className="ml-1 text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-medium">
                  {prescriptions.length}가지
                </span>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addPrescription}
                className="text-blue-600 border-blue-200 hover:bg-blue-50 text-xs"
              >
                + 약물 추가
              </Button>
            </div>
            <div className="px-6 py-5 space-y-4">
              {prescriptions.map((p, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-zinc-100 bg-zinc-50/50 p-4 space-y-3"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wide">
                      약물 {idx + 1}
                    </span>
                    {prescriptions.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removePrescription(idx)}
                        className="text-xs text-red-400 hover:text-red-600 transition-colors"
                      >
                        삭제
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-xs text-zinc-500">약물명</Label>
                      <Input
                        placeholder="예: 암로디핀"
                        value={p.medication_name}
                        onChange={(e) => setPrescField(idx, "medication_name", e.target.value)}
                        className="h-9 bg-white"
                        required
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs text-zinc-500">용량</Label>
                      <Input
                        placeholder="예: 5mg"
                        value={p.dosage}
                        onChange={(e) => setPrescField(idx, "dosage", e.target.value)}
                        className="h-9 bg-white"
                        required
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs text-zinc-500">복용 횟수</Label>
                      <Input
                        placeholder="예: 1일 1회"
                        value={p.frequency}
                        onChange={(e) => setPrescField(idx, "frequency", e.target.value)}
                        className="h-9 bg-white"
                        required
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs text-zinc-500">복용 기간 (일)</Label>
                      <Input
                        type="number"
                        min={1}
                        value={p.duration_days}
                        onChange={(e) => setPrescField(idx, "duration_days", Number(e.target.value))}
                        className="h-9 bg-white"
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <Label className="text-xs text-zinc-500">
                      특이사항 <span className="text-zinc-300">(선택)</span>
                    </Label>
                    <Input
                      placeholder="예: 식후 30분 복용, 공복 금지"
                      value={p.instructions}
                      onChange={(e) => setPrescField(idx, "instructions", e.target.value)}
                      className="h-9 bg-white"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 제출 */}
          <Button
            type="submit"
            className="w-full h-12 bg-blue-700 hover:bg-blue-800 text-base font-semibold rounded-xl"
            disabled={loading}
          >
            {loading ? "등록 중..." : "진료 기록 등록하기"}
          </Button>
        </form>
      </main>
    </div>
  );
}
