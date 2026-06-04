"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { getUser, getToken, logout } from "@/lib/auth";
import type { User } from "@/lib/api";

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const [user, setUser] = useState<User | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setUser(getUser());
  }, []);

  useEffect(() => {
    if (!user) return;
    const token = getToken();
    if (!token) return;

    const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const es = new EventSource(`${baseUrl}/api/v1/notifications/stream?token=${token}`);
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setUnreadCount(data.count ?? 0);
      } catch {}
    };
    es.onerror = () => es.close();
    return () => es.close();
  }, [user]);

  function handleLogout() {
    logout();
    toast.success("로그아웃됐어요.");
    router.push("/login");
  }

  const navLink = (href: string, label: string) => (
    <Link
      href={href}
      className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
        pathname.startsWith(href)
          ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
          : "text-zinc-600 hover:bg-zinc-50 dark:text-zinc-400 dark:hover:bg-zinc-800"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-200 dark:border-zinc-800 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-sm px-6 py-0">
      <div className="max-w-5xl mx-auto flex items-center justify-between h-14">
        <Link href="/dashboard" className="flex items-center gap-2 font-bold text-blue-700 dark:text-blue-400 text-lg">
          💊 MediGuide AI
        </Link>

        {user && (
          <nav className="flex items-center gap-1">
            {navLink("/dashboard", "대시보드")}
            {navLink("/records", "진료기록")}
            {navLink("/messages", "메시지")}
            {navLink("/appointments", "예약")}
            {user.role === "PATIENT" && navLink("/health-logs", "건강일지")}
            {user.role === "PATIENT" && navLink("/health-goals/goals", "건강목표")}
            {user.role === "PATIENT" && navLink("/health-reports", "건강리포트")}
            {user.role === "PATIENT" && navLink("/vitals", "바이탈")}
            {user.role === "PATIENT" && navLink("/symptom-check", "증상 체크")}
            {user.role === "PATIENT" && navLink("/reminders", "복약알림")}
            {user.role === "PATIENT" && navLink("/chat", "AI 채팅")}

            {user.role === "DOCTOR" && (
              <Link href="/records/new">
                <Button size="sm" className="ml-2 bg-blue-700 hover:bg-blue-800 h-8 text-xs">
                  + 진료기록 등록
                </Button>
              </Link>
            )}

            <button
              onClick={() => router.push("/notifications")}
              className="relative ml-1 p-1.5 rounded-md text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
              aria-label="알림"
            >
              <span className="text-lg">🔔</span>
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-0.5">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </button>

            {mounted && (
              <button
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                className="ml-1 p-1.5 rounded-md text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
                aria-label="테마 변경"
              >
                <span className="text-lg">{theme === "dark" ? "☀️" : "🌙"}</span>
              </button>
            )}

            <div className="ml-4 flex items-center gap-3 pl-4 border-l border-zinc-200 dark:border-zinc-700">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-zinc-800 dark:text-zinc-200 leading-none">{user.name}</p>
                <p className="text-xs text-zinc-400 mt-0.5">{user.role === "DOCTOR" ? "의사" : "환자"}</p>
              </div>
              <Link href="/profile" className="text-xs text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 transition-colors">
                프로필
              </Link>
              <button
                onClick={handleLogout}
                className="text-xs text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 transition-colors"
              >
                로그아웃
              </button>
            </div>
          </nav>
        )}
      </div>
    </header>
  );
}