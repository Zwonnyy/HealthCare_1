"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { authApi, userApi } from "@/lib/api";
import { saveToken, saveUser } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await authApi.login(email, password);
      saveToken(data.access_token);
      const { data: user } = await userApi.me();
      saveUser(user);
      toast.success("로그인됐어요.");
      router.push("/records");
    } catch {
      toast.error("이메일 또는 비밀번호를 확인해주세요.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* 왼쪽 브랜딩 패널 */}
      <div className="hidden lg:flex flex-col justify-between bg-blue-700 text-white p-12">
        <div className="text-2xl font-bold tracking-tight">💊 MediGuide AI</div>
        <div className="space-y-4">
          <h1 className="text-4xl font-bold leading-tight">
            진료 기록 기반<br />AI 복약 안내 시스템
          </h1>
          <p className="text-blue-200 text-lg leading-relaxed">
            처방 약물 정보와 생활습관 개선 가이드를<br />
            Claude AI가 자동으로 생성해드립니다.
          </p>
        </div>
        <div className="flex gap-6 text-sm text-blue-200">
          <span>✓ AI 복약 안내</span>
          <span>✓ 생활습관 가이드</span>
          <span>✓ 실시간 생성</span>
        </div>
      </div>

      {/* 오른쪽 로그인 폼 */}
      <div className="flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-sm space-y-8">
          <div>
            <h2 className="text-3xl font-bold text-zinc-900">로그인</h2>
            <p className="text-zinc-500 mt-2 text-sm">계속하려면 로그인하세요.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-700 font-medium">이메일</Label>
              <Input
                id="email"
                type="email"
                placeholder="example@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-11"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-zinc-700 font-medium">비밀번호</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11"
                required
              />
            </div>
            <Button type="submit" className="w-full h-11 bg-blue-700 hover:bg-blue-800 text-base" disabled={loading}>
              {loading ? "로그인 중..." : "로그인"}
            </Button>
          </form>

          <p className="text-center text-sm text-zinc-500">
            계정이 없으신가요?{" "}
            <Link href="/signup" className="text-blue-600 hover:underline font-medium">
              회원가입
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}