"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { authApi } from "@/lib/api";
import type { UserRole } from "@/lib/api";
import { getErrorMessage } from "@/lib/error";

export default function SignupPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    email: "",
    password: "",
    name: "",
    gender: "MALE",
    birth_date: "",
    phone_number: "",
    role: "PATIENT" as UserRole,
  });

  function set(key: string, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.signup(form);
      toast.success("회원가입 완료! 로그인해주세요.");
      router.push("/login");
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, "회원가입에 실패했어요."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen grid bg-white dark:bg-zinc-950 lg:grid-cols-2">
      {/* 왼쪽 브랜딩 */}
      <div className="hidden lg:flex flex-col justify-between bg-blue-700 text-white p-12 dark:border-r dark:border-zinc-800 dark:bg-[radial-gradient(circle_at_25%_20%,rgba(37,99,235,0.35),transparent_32%),linear-gradient(135deg,#09090b,#111827_58%,#0f172a)]">
        <div className="text-2xl font-bold tracking-tight">💊 MediGuide AI</div>
        <div className="space-y-4">
          <h1 className="text-4xl font-bold leading-tight">
            지금 시작하세요
          </h1>
          <ul className="space-y-3 text-blue-100 text-base dark:text-zinc-300">
            <li className="flex items-start gap-3">
              <span className="mt-0.5">🩺</span>
              <span><b className="text-white">의사</b> — 진료 기록과 처방을 등록하고 환자에게 공유</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="mt-0.5">👤</span>
              <span><b className="text-white">환자</b> — AI가 생성한 복약 안내와 생활습관 가이드 수령</span>
            </li>
          </ul>
        </div>
        <p className="text-blue-100 text-xs dark:text-zinc-400">※ 이 서비스는 참고용이며 실제 의료 결정은 의사와 상담하세요.</p>
      </div>

      {/* 오른쪽 폼 */}
      <div className="flex items-center justify-center p-8 bg-white dark:bg-zinc-950 overflow-y-auto">
        <div className="w-full max-w-sm space-y-6 py-4">
          <div>
            <h2 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">회원가입</h2>
            <p className="text-zinc-500 dark:text-zinc-400 mt-2 text-sm">역할을 선택하고 계정을 만드세요.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 역할 */}
            <div className="space-y-2">
              <Label className="font-medium text-zinc-700 dark:text-zinc-300">역할</Label>
              <div className="grid grid-cols-2 gap-2">
                {(["PATIENT", "DOCTOR"] as UserRole[]).map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => set("role", r)}
                    className={`border rounded-lg py-3 text-sm font-medium transition-all ${
                      form.role === r
                        ? "border-blue-600 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400"
                        : "border-zinc-200 dark:border-zinc-700 text-zinc-500 dark:text-zinc-400 hover:border-zinc-300 dark:hover:border-zinc-600"
                    }`}
                  >
                    {r === "PATIENT" ? "👤 환자" : "🩺 의사"}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label className="font-medium text-zinc-700 dark:text-zinc-300">이름</Label>
              <Input value={form.name} onChange={(e) => set("name", e.target.value)} className="h-10 text-zinc-900 dark:text-zinc-100 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600" required />
            </div>
            <div className="space-y-2">
              <Label className="font-medium text-zinc-700 dark:text-zinc-300">이메일</Label>
              <Input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} className="h-10 text-zinc-900 dark:text-zinc-100 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600" required />
            </div>
            <div className="space-y-2">
              <Label className="font-medium text-zinc-700 dark:text-zinc-300">비밀번호 <span className="text-zinc-400 font-normal">(8자 이상)</span></Label>
              <Input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} className="h-10 text-zinc-900 dark:text-zinc-100 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600" required />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label className="font-medium text-zinc-700 dark:text-zinc-300">성별</Label>
                <Select value={form.gender} onValueChange={(v) => v && set("gender", v)}>
                  <SelectTrigger className="h-10 text-zinc-900 dark:text-zinc-100 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MALE">남성</SelectItem>
                    <SelectItem value="FEMALE">여성</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="font-medium text-zinc-700 dark:text-zinc-300">생년월일</Label>
                <Input type="date" value={form.birth_date} onChange={(e) => set("birth_date", e.target.value)} className="h-10 text-zinc-900 dark:text-zinc-100 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600" required />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="font-medium text-zinc-700 dark:text-zinc-300">전화번호</Label>
              <Input placeholder="01012345678" value={form.phone_number} onChange={(e) => set("phone_number", e.target.value)} className="h-10 text-zinc-900 dark:text-zinc-100 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600" required />
            </div>

            <Button type="submit" className="w-full h-11 bg-blue-700 hover:bg-blue-800 text-base mt-2" disabled={loading}>
              {loading ? "처리 중..." : "회원가입"}
            </Button>
          </form>

          <p className="text-center text-sm text-zinc-500 dark:text-zinc-400">
            이미 계정이 있으신가요?{" "}
            <Link href="/login" className="text-blue-600 hover:underline font-medium dark:text-blue-400">로그인</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
