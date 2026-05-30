"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import Navbar from "@/components/Navbar";
import { statsApi, PatientStats, DoctorStats } from "@/lib/api";
import { getToken, getUser } from "@/lib/auth";

const MOOD_EMOJI: Record<string, string> = {
  GREAT: "😄",
  GOOD: "🙂",
  NORMAL: "😐",
  BAD: "😕",
  TERRIBLE: "😢",
};

const MOOD_LABEL: Record<string, string> = {
  GREAT: "매우 좋음",
  GOOD: "좋음",
  NORMAL: "보통",
  BAD: "나쁨",
  TERRIBLE: "매우 나쁨",
};

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white border border-zinc-100 rounded-xl p-5">
      <p className="text-sm text-zinc-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-zinc-900">{value}</p>
      {sub && <p className="text-xs text-zinc-400 mt-1">{sub}</p>}
    </div>
  );
}

function SkeletonCard() {
  return <div className="h-24 rounded-xl bg-zinc-200 animate-pulse" />;
}

export default function DashboardPage() {
  const router = useRouter();
  const user = getUser();
  const [patientStats, setPatientStats] = useState<PatientStats | null>(null);
  const [doctorStats, setDoctorStats] = useState<DoctorStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    if (!user) return;

    if (user.role === "PATIENT") {
      statsApi
        .patient()
        .then(({ data }) => setPatientStats(data))
        .catch(() => toast.error("통계를 불러오지 못했어요."))
        .finally(() => setLoading(false));
    } else {
      statsApi
        .doctor()
        .then(({ data }) => setDoctorStats(data))
        .catch(() => toast.error("통계를 불러오지 못했어요."))
        .finally(() => setLoading(false));
    }
  }, [router]);

  function renderMoodBar(dist: PatientStats["mood_distribution_30d"]) {
    const moods = ["GREAT", "GOOD", "NORMAL", "BAD", "TERRIBLE"] as const;
    const total = moods.reduce((s, m) => s + dist[m], 0);
    if (total === 0) return <p className="text-sm text-zinc-400">최근 30일 기록 없음</p>;

    return (
      <div className="space-y-2">
        {moods.map((m) => {
          const pct = total > 0 ? Math.round((dist[m] / total) * 100) : 0;
          return (
            <div key={m} className="flex items-center gap-3">
              <span className="text-base w-6">{MOOD_EMOJI[m]}</span>
              <span className="text-xs text-zinc-500 w-16">{MOOD_LABEL[m]}</span>
              <div className="flex-1 bg-zinc-100 rounded-full h-2">
                <div
                  className="bg-blue-400 h-2 rounded-full transition-all"
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="text-xs text-zinc-400 w-10 text-right">{pct}%</span>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-10">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-zinc-900">
            {user?.name}님, 안녕하세요 👋
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            {user?.role === "DOCTOR" ? "의사 대시보드" : "환자 대시보드"}
          </p>
        </div>

        {loading && (
          <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {!loading && user?.role === "DOCTOR" && doctorStats && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <StatCard label="총 환자 수" value={doctorStats.total_patients} sub="명" />
              <StatCard label="총 진료기록 수" value={doctorStats.total_records} sub="건" />
              <StatCard label="최근 30일 진료기록" value={doctorStats.records_last_30d} sub="건" />
              <StatCard label="미읽은 메시지" value={doctorStats.unread_messages} sub="건" />
            </div>
            <div className="bg-white border border-zinc-100 rounded-xl p-5">
              <p className="text-sm text-zinc-500 mb-1">대기 중인 AI 가이드</p>
              <p className="text-2xl font-bold text-amber-600">{doctorStats.pending_guides}</p>
              <p className="text-xs text-zinc-400 mt-1">건</p>
            </div>
          </div>
        )}

        {!loading && user?.role === "PATIENT" && patientStats && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <StatCard label="총 진료기록 수" value={patientStats.total_records} sub="건" />
              <StatCard label="미읽은 메시지" value={patientStats.unread_messages} sub="건" />
              <StatCard
                label="건강일지 총 수"
                value={patientStats.health_log_stats.total}
                sub="건"
              />
              <StatCard
                label="7일 평균 통증 점수"
                value={
                  patientStats.health_log_stats.avg_pain_score_7d != null
                    ? patientStats.health_log_stats.avg_pain_score_7d.toFixed(1)
                    : "-"
                }
                sub="/ 10점"
              />
            </div>

            <div className="bg-white border border-zinc-100 rounded-xl p-5">
              <p className="text-sm font-medium text-zinc-700 mb-1">30일 평균 통증 점수</p>
              <p className="text-2xl font-bold text-zinc-900">
                {patientStats.health_log_stats.avg_pain_score_30d != null
                  ? patientStats.health_log_stats.avg_pain_score_30d.toFixed(1)
                  : "-"}
              </p>
              <p className="text-xs text-zinc-400 mt-1">/ 10점</p>
            </div>

            <div className="bg-white border border-zinc-100 rounded-xl p-5">
              <p className="text-sm font-medium text-zinc-700 mb-4">최근 30일 기분 분포</p>
              {renderMoodBar(patientStats.mood_distribution_30d)}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
