"use client";
import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Navbar from "@/components/Navbar";
import { reminderApi, type MedicationReminder } from "@/lib/api";

export default function RemindersPage() {
  const [reminders, setReminders] = useState<MedicationReminder[]>([]);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState("");
  const [time, setTime] = useState("08:00");
  const [submitting, setSubmitting] = useState(false);

  const fetchReminders = useCallback(async () => {
    setLoading(true);
    try {
      const res = await reminderApi.list();
      setReminders(res.data);
    } catch {
      toast.error("알림 목록을 불러오지 못했어요.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchReminders(); }, [fetchReminders]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) { toast.error("약 이름을 입력해주세요."); return; }
    if (!/^\d{2}:\d{2}$/.test(time)) { toast.error("시간을 HH:MM 형식으로 입력해주세요."); return; }
    setSubmitting(true);
    try {
      const res = await reminderApi.create({ name: name.trim(), reminder_time: time });
      setReminders((prev) => [...prev, res.data]);
      setName("");
      setTime("08:00");
      toast.success("복약 알림이 추가됐어요.");
    } catch {
      toast.error("추가에 실패했어요.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleToggle(reminder: MedicationReminder) {
    try {
      const res = await reminderApi.update(reminder.id, { enabled: !reminder.enabled });
      setReminders((prev) => prev.map((r) => (r.id === reminder.id ? res.data : r)));
      toast.success(res.data.enabled ? "알림을 켰어요." : "알림을 껐어요.");
    } catch {
      toast.error("변경에 실패했어요.");
    }
  }

  async function handleDelete(id: number) {
    try {
      await reminderApi.delete(id);
      setReminders((prev) => prev.filter((r) => r.id !== id));
      toast.success("알림이 삭제됐어요.");
    } catch {
      toast.error("삭제에 실패했어요.");
    }
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      <Navbar />
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">복약 알림 설정</h1>
        <p className="text-sm text-zinc-500 mt-1">설정한 시간에 인앱 알림으로 복약을 상기시켜 드려요.</p>
      </div>

      <form onSubmit={handleCreate} className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-6 space-y-4">
        <h2 className="font-semibold text-zinc-800 dark:text-zinc-200">새 알림 추가</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1">
            <Label className="text-zinc-700 dark:text-zinc-300">약 이름</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="예: 암로디핀 5mg"
              className="text-zinc-900 dark:text-zinc-100 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-zinc-700 dark:text-zinc-300">알림 시간</Label>
            <Input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="text-zinc-900 dark:text-zinc-100 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600"
            />
          </div>
        </div>
        <Button type="submit" disabled={submitting} className="w-full bg-blue-700 hover:bg-blue-800">
          {submitting ? "추가 중..." : "알림 추가"}
        </Button>
      </form>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-zinc-800 dark:text-zinc-200">등록된 알림</h2>
        {loading && <p className="text-sm text-zinc-400">불러오는 중...</p>}
        {!loading && reminders.length === 0 && (
          <div className="text-center py-10 text-zinc-400 text-sm">
            <p className="text-3xl mb-2">💊</p>
            <p>등록된 복약 알림이 없어요.</p>
          </div>
        )}
        {reminders.map((r) => (
          <div
            key={r.id}
            className={`flex items-center justify-between rounded-xl border p-4 transition-colors ${
              r.enabled
                ? "border-blue-200 bg-blue-50 dark:bg-blue-950/20 dark:border-blue-800"
                : "border-zinc-200 bg-zinc-50 dark:bg-zinc-800/50 dark:border-zinc-700"
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">{r.enabled ? "🔔" : "🔕"}</span>
              <div>
                <p className={`font-medium ${r.enabled ? "text-zinc-900 dark:text-zinc-100" : "text-zinc-400"}`}>{r.name}</p>
                <p className="text-sm text-zinc-500">{r.reminder_time}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleToggle(r)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  r.enabled ? "bg-blue-600" : "bg-zinc-300 dark:bg-zinc-600"
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${r.enabled ? "translate-x-6" : "translate-x-1"}`} />
              </button>
              <button
                onClick={() => handleDelete(r.id)}
                className="text-zinc-400 hover:text-red-500 dark:hover:text-red-400 transition-colors text-sm px-2"
              >
                삭제
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
    </div>
  );
}
