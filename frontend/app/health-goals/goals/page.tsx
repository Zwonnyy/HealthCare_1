"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Navbar from "@/components/Navbar";
import { healthGoalApi, HealthGoal, HealthGoalHistoryPoint, GoalType } from "@/lib/api";
import { getToken, getUser } from "@/lib/auth";

const GOAL_TYPE_OPTIONS: { value: GoalType; label: string; emoji: string; defaultUnit: string }[] = [
  { value: "WEIGHT",         label: "체중",     emoji: "⚖️",  defaultUnit: "kg" },
  { value: "BLOOD_PRESSURE", label: "혈압",     emoji: "🩺",  defaultUnit: "mmHg" },
  { value: "EXERCISE_DAYS",  label: "운동 일수", emoji: "🏃",  defaultUnit: "일/월" },
  { value: "PAIN_SCORE",     label: "통증 점수", emoji: "💊",  defaultUnit: "점" },
  { value: "CUSTOM",         label: "직접 입력", emoji: "🎯",  defaultUnit: "" },
];

function progressPct(goal: HealthGoal): number {
  if (goal.current_value === null || goal.current_value === undefined) return 0;
  if (goal.target_value === 0) return 0;
  return Math.min(Math.round((goal.current_value / goal.target_value) * 100), 100);
}

function progressColor(pct: number) {
  if (pct >= 100) return "bg-emerald-500";
  if (pct >= 60) return "bg-blue-500";
  return "bg-amber-400";
}

export default function HealthGoalsPage() {
  const router = useRouter();
  const user = getUser();

  const [goals, setGoals] = useState<HealthGoal[]>([]);
  const [loading, setLoading] = useState(true);

  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    goal_type: "WEIGHT" as GoalType,
    title: "",
    target_value: "",
    unit: "kg",
    deadline: "",
  });

  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [newValue, setNewValue] = useState<Record<number, string>>({});

  const [chartGoalId, setChartGoalId] = useState<number | null>(null);
  const [chartData, setChartData] = useState<HealthGoalHistoryPoint[]>([]);
  const [chartLoading, setChartLoading] = useState(false);

  const load = useCallback(() => {
    healthGoalApi.list()
      .then(({ data }) => setGoals(data))
      .catch(() => toast.error("목표를 불러오지 못했어요."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    if (user?.role !== "PATIENT") { router.replace("/dashboard"); return; }
    load();
  }, [router, load]);

  function handleTypeChange(type: GoalType) {
    const opt = GOAL_TYPE_OPTIONS.find((o) => o.value === type)!;
    setForm((f) => ({ ...f, goal_type: type, unit: opt.defaultUnit, title: opt.label }));
  }

  async function handleCreate() {
    if (!form.title.trim() || !form.target_value) { toast.error("목표 제목과 목표치를 입력해주세요."); return; }
    setCreating(true);
    try {
      await healthGoalApi.create({
        goal_type: form.goal_type,
        title: form.title.trim(),
        target_value: Number(form.target_value),
        unit: form.unit,
        deadline: form.deadline || undefined,
      });
      toast.success("목표를 설정했어요.");
      setShowCreate(false);
      setForm({ goal_type: "WEIGHT", title: "체중", target_value: "", unit: "kg", deadline: "" });
      load();
    } catch {
      toast.error("목표 설정에 실패했어요.");
    } finally {
      setCreating(false);
    }
  }

  async function handleUpdateValue(goal: HealthGoal) {
    const val = newValue[goal.id];
    if (!val) return;
    setUpdatingId(goal.id);
    try {
      const updated = await healthGoalApi.update(goal.id, { current_value: Number(val) });
      setGoals((prev) => prev.map((g) => g.id === goal.id ? updated.data : g));
      setNewValue((prev) => { const n = { ...prev }; delete n[goal.id]; return n; });
      toast.success("진행 상황을 업데이트했어요.");
    } catch {
      toast.error("업데이트에 실패했어요.");
    } finally {
      setUpdatingId(null);
    }
  }

  async function handleAchieve(goal: HealthGoal) {
    try {
      const updated = await healthGoalApi.update(goal.id, { achieved: !goal.achieved });
      setGoals((prev) => prev.map((g) => g.id === goal.id ? updated.data : g));
      toast.success(goal.achieved ? "목표를 다시 진행 중으로 변경했어요." : "🎉 목표를 달성했어요!");
    } catch {
      toast.error("업데이트에 실패했어요.");
    }
  }

  async function handleOpenChart(goal: HealthGoal) {
    setChartGoalId(goal.id);
    setChartLoading(true);
    try {
      const { data } = await healthGoalApi.history(goal.id);
      setChartData(data);
    } catch {
      toast.error("차트 데이터를 불러오지 못했어요.");
    } finally {
      setChartLoading(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("목표를 삭제할까요?")) return;
    try {
      await healthGoalApi.delete(id);
      setGoals((prev) => prev.filter((g) => g.id !== id));
      toast.success("삭제됐어요.");
    } catch {
      toast.error("삭제에 실패했어요.");
    }
  }

  const active = goals.filter((g) => !g.achieved);
  const achieved = goals.filter((g) => g.achieved);

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">건강 목표</h1>
            <p className="text-sm text-zinc-500 mt-1">목표를 설정하고 달성률을 추적하세요.</p>
          </div>
          <Button onClick={() => setShowCreate(true)} className="bg-blue-700 hover:bg-blue-800">
            + 목표 추가
          </Button>
        </div>

        {loading && (
          <div className="space-y-3">
            {[1, 2].map((i) => <div key={i} className="h-32 rounded-xl bg-zinc-200 dark:bg-zinc-800 animate-pulse" />)}
          </div>
        )}

        {!loading && goals.length === 0 && (
          <div className="text-center py-20 text-zinc-400">
            <p className="text-5xl mb-4">🎯</p>
            <p className="text-lg font-medium">설정된 목표가 없어요</p>
            <Button className="mt-4 bg-blue-700 hover:bg-blue-800" onClick={() => setShowCreate(true)}>첫 목표 설정하기</Button>
          </div>
        )}

        {active.length > 0 && (
          <div className="space-y-3 mb-8">
            <h2 className="text-sm font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide">진행 중</h2>
            {active.map((goal) => {
              const pct = progressPct(goal);
              const opt = GOAL_TYPE_OPTIONS.find((o) => o.value === goal.goal_type)!;
              return (
                <div key={goal.id} className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 rounded-xl p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{opt.emoji}</span>
                      <div>
                        <p className="font-semibold text-zinc-900 dark:text-zinc-100">{goal.title}</p>
                        <p className="text-xs text-zinc-400">
                          목표: {goal.target_value} {goal.unit}
                          {goal.deadline && ` · D-${Math.max(0, Math.ceil((new Date(goal.deadline).getTime() - Date.now()) / 86400000))}일`}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-1 items-center">
                      <button onClick={() => handleOpenChart(goal)} className="text-xs text-blue-500 dark:text-blue-400 hover:underline">📈 추이</button>
                      <span className="text-zinc-300 dark:text-zinc-600">·</span>
                      <button onClick={() => handleAchieve(goal)} className="text-xs text-emerald-600 dark:text-emerald-400 hover:underline">달성</button>
                      <span className="text-zinc-300 dark:text-zinc-600">·</span>
                      <button onClick={() => handleDelete(goal.id)} className="text-xs text-zinc-400 hover:text-red-500">삭제</button>
                    </div>
                  </div>

                  <div className="mb-3">
                    <div className="flex justify-between text-xs text-zinc-500 dark:text-zinc-400 mb-1">
                      <span>현재: {goal.current_value ?? "미입력"} {goal.unit}</span>
                      <span>{pct}%</span>
                    </div>
                    <div className="w-full bg-zinc-100 dark:bg-zinc-700 rounded-full h-2">
                      <div className={`h-2 rounded-full transition-all ${progressColor(pct)}`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Input
                      type="number"
                      placeholder={`현재 ${goal.unit} 입력`}
                      value={newValue[goal.id] ?? ""}
                      onChange={(e) => setNewValue((prev) => ({ ...prev, [goal.id]: e.target.value }))}
                      className="text-sm h-8 dark:bg-zinc-700 dark:border-zinc-600"
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-8 text-xs shrink-0 dark:border-zinc-600 dark:text-zinc-300"
                      onClick={() => handleUpdateValue(goal)}
                      disabled={!newValue[goal.id] || updatingId === goal.id}
                    >
                      {updatingId === goal.id ? "…" : "업데이트"}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {achieved.length > 0 && (
          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide">달성 완료 🎉</h2>
            {achieved.map((goal) => {
              const opt = GOAL_TYPE_OPTIONS.find((o) => o.value === goal.goal_type)!;
              return (
                <div key={goal.id} className="bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-800 rounded-xl p-4 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{opt.emoji}</span>
                    <div>
                      <p className="font-medium text-zinc-700 dark:text-zinc-300 line-through">{goal.title}</p>
                      <p className="text-xs text-emerald-600 dark:text-emerald-400">목표 달성! {goal.target_value} {goal.unit}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleAchieve(goal)} className="text-xs text-zinc-400 hover:text-zinc-600">되돌리기</button>
                    <button onClick={() => handleDelete(goal.id)} className="text-xs text-zinc-400 hover:text-red-500">삭제</button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {chartGoalId !== null && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white dark:bg-zinc-800 rounded-2xl shadow-xl w-full max-w-lg p-6">
              {(() => {
                const goal = goals.find((g) => g.id === chartGoalId);
                const opt = GOAL_TYPE_OPTIONS.find((o) => o.value === goal?.goal_type);
                return (
                  <>
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
                        {opt?.emoji} {goal?.title} 추이
                      </h2>
                      <button
                        onClick={() => { setChartGoalId(null); setChartData([]); }}
                        className="text-zinc-400 hover:text-zinc-600 text-xl leading-none"
                      >×</button>
                    </div>

                    {chartLoading ? (
                      <div className="h-48 flex items-center justify-center text-zinc-400 text-sm animate-pulse">차트 불러오는 중...</div>
                    ) : chartData.length === 0 ? (
                      <div className="h-48 flex flex-col items-center justify-center text-zinc-400">
                        <p className="text-3xl mb-2">📊</p>
                        <p className="text-sm">아직 기록된 수치가 없어요.</p>
                        <p className="text-xs mt-1">현재값을 업데이트하면 차트에 표시돼요.</p>
                      </div>
                    ) : (
                      <div className="h-56">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={chartData.map((p) => ({
                            date: new Date(p.recorded_at).toLocaleDateString("ko-KR", { month: "short", day: "numeric" }),
                            value: p.recorded_value,
                          }))}>
                            <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                            <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" domain={["auto", "auto"]} />
                            <Tooltip
                              formatter={(v) => [`${v} ${goal?.unit}`, "수치"]}
                              contentStyle={{ fontSize: 12, borderRadius: 8 }}
                            />
                            {goal && (
                              <ReferenceLine
                                y={goal.target_value}
                                stroke="#3b82f6"
                                strokeDasharray="4 2"
                                label={{ value: `목표 ${goal.target_value}${goal.unit}`, fontSize: 10, fill: "#3b82f6", position: "insideTopRight" }}
                              />
                            )}
                            <Line
                              type="monotone"
                              dataKey="value"
                              stroke="#10b981"
                              strokeWidth={2}
                              dot={{ r: 4, fill: "#10b981" }}
                              activeDot={{ r: 6 }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </>
                );
              })()}
            </div>
          </div>
        )}

        {showCreate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white dark:bg-zinc-800 rounded-2xl shadow-xl w-full max-w-md p-6">
              <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 mb-4">목표 설정</h2>
              <div className="space-y-4">
                <div>
                  <Label className="mb-2">목표 유형</Label>
                  <div className="grid grid-cols-3 gap-2">
                    {GOAL_TYPE_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => handleTypeChange(opt.value)}
                        className={`flex flex-col items-center gap-1 py-2 px-1 rounded-lg border text-xs transition-colors ${
                          form.goal_type === opt.value
                            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400"
                            : "border-zinc-200 dark:border-zinc-600 text-zinc-600 dark:text-zinc-400 hover:border-zinc-300"
                        }`}
                      >
                        <span className="text-lg">{opt.emoji}</span>
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <Label className="mb-1.5">목표 제목</Label>
                  <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="dark:bg-zinc-700 dark:border-zinc-600" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="mb-1.5">목표치</Label>
                    <Input type="number" value={form.target_value} onChange={(e) => setForm({ ...form, target_value: e.target.value })} className="dark:bg-zinc-700 dark:border-zinc-600" />
                  </div>
                  <div>
                    <Label className="mb-1.5">단위</Label>
                    <Input value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} className="dark:bg-zinc-700 dark:border-zinc-600" />
                  </div>
                </div>
                <div>
                  <Label className="mb-1.5">목표 날짜 (선택)</Label>
                  <Input type="date" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} className="dark:bg-zinc-700 dark:border-zinc-600" />
                </div>
              </div>
              <div className="flex gap-2 mt-6">
                <Button variant="outline" className="flex-1" onClick={() => setShowCreate(false)}>취소</Button>
                <Button className="flex-1 bg-blue-700 hover:bg-blue-800" onClick={handleCreate} disabled={creating}>
                  {creating ? "저장 중…" : "목표 설정"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
