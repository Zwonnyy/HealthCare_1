"use client";
import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Navbar from "@/components/Navbar";
import { vitalApi, type VitalRecord } from "@/lib/api";

const FIELD_CONFIG = [
  { key: "systolic", label: "수축기 혈압", unit: "mmHg", placeholder: "예: 120" },
  { key: "diastolic", label: "이완기 혈압", unit: "mmHg", placeholder: "예: 80" },
  { key: "blood_sugar", label: "혈당", unit: "mg/dL", placeholder: "예: 95" },
  { key: "weight", label: "체중", unit: "kg", placeholder: "예: 68.5" },
  { key: "heart_rate", label: "심박수", unit: "bpm", placeholder: "예: 72" },
] as const;

type VitalKey = (typeof FIELD_CONFIG)[number]["key"];

export default function VitalsPage() {
  const [mounted, setMounted] = useState(false);
  const [vitals, setVitals] = useState<VitalRecord[]>([]);
  const [form, setForm] = useState<Partial<Record<VitalKey, string>>>({});
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchVitals = useCallback(async () => {
    setLoading(true);
    try {
      const res = await vitalApi.list(30);
      setVitals(res.data);
    } catch {
      toast.error("바이탈 기록을 불러오지 못했어요.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setMounted(true);
    fetchVitals();
  }, [fetchVitals]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload: Record<string, number | string> = {};
    for (const f of FIELD_CONFIG) {
      const v = form[f.key];
      if (v && v.trim()) payload[f.key] = parseFloat(v);
    }
    if (Object.keys(payload).length === 0) {
      toast.error("하나 이상의 수치를 입력해주세요.");
      return;
    }
    if (notes.trim()) payload.notes = notes.trim();
    setSubmitting(true);
    try {
      const res = await vitalApi.record(payload);
      setVitals((prev) => [res.data, ...prev]);
      setForm({});
      setNotes("");
      if (res.data.alert_message) {
        toast.warning(res.data.alert_message, { duration: 8000 });
      } else {
        toast.success("바이탈이 기록됐어요.");
      }
    } catch {
      toast.error("기록에 실패했어요.");
    } finally {
      setSubmitting(false);
    }
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleString("ko-KR", {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      <Navbar />
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">건강 바이탈 기록</h1>
        <p className="text-sm text-zinc-500 mt-1">혈압, 혈당, 체중 등을 입력하면 AI가 이상 여부를 감지해요.</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-6 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {FIELD_CONFIG.map((f) => (
            <div key={f.key} className="space-y-1">
              <Label className="text-zinc-700 dark:text-zinc-300">{f.label} <span className="text-zinc-400 text-xs">({f.unit})</span></Label>
              <Input
                type="number"
                step="any"
                placeholder={f.placeholder}
                value={form[f.key] ?? ""}
                onChange={(e) => setForm((prev) => ({ ...prev, [f.key]: e.target.value }))}
                className="text-zinc-900 dark:text-zinc-100 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600"
              />
            </div>
          ))}
          <div className="space-y-1 sm:col-span-2">
            <Label className="text-zinc-700 dark:text-zinc-300">메모 (선택)</Label>
            <Input
              placeholder="특이사항 입력"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="text-zinc-900 dark:text-zinc-100 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600"
            />
          </div>
        </div>
        <Button type="submit" disabled={submitting} className="w-full bg-blue-700 hover:bg-blue-800">
          {submitting ? "분석 중..." : "기록하기"}
        </Button>
      </form>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-zinc-800 dark:text-zinc-200">최근 기록</h2>
        {loading && <p className="text-sm text-zinc-400">불러오는 중...</p>}
        {!loading && vitals.length === 0 && (
          <p className="text-sm text-zinc-400">아직 기록이 없어요.</p>
        )}
        {vitals.map((v) => (
          <div
            key={v.id}
            className={`rounded-xl border p-4 ${
              v.alert_message
                ? "border-amber-300 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-700"
                : "border-zinc-200 bg-white dark:bg-zinc-900 dark:border-zinc-700"
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-zinc-400" suppressHydrationWarning>
                {mounted ? formatDate(v.recorded_at) : ""}
              </span>
              {v.alert_message && <span className="text-xs font-medium text-amber-600 dark:text-amber-400">⚠ 이상 감지</span>}
            </div>
            <div className="flex flex-wrap gap-3 text-sm">
              {v.systolic != null && <span className="bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded">혈압 {v.systolic}/{v.diastolic} mmHg</span>}
              {v.blood_sugar != null && <span className="bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded">혈당 {v.blood_sugar} mg/dL</span>}
              {v.weight != null && <span className="bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded">체중 {v.weight} kg</span>}
              {v.heart_rate != null && <span className="bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded">심박수 {v.heart_rate} bpm</span>}
            </div>
            {v.alert_message && (
              <p className="mt-2 text-sm text-amber-700 dark:text-amber-300">{v.alert_message}</p>
            )}
            {v.notes && <p className="mt-1 text-xs text-zinc-500">{v.notes}</p>}
          </div>
        ))}
      </div>
    </div>
    </div>
  );
}
