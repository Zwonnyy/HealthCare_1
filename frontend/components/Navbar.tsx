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
  const [healthMenuOpen, setHealthMenuOpen] = useState(false);

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

  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);

  const navLink = (href: string, label: string) => (
    <Link
      href={href}
      className={`px-3 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
        isActive(href)
          ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
          : "text-zinc-600 hover:bg-zinc-50 dark:text-zinc-400 dark:hover:bg-zinc-800"
      }`}
    >
      {label}
    </Link>
  );

  const healthLinks = [
    ["/health-logs", "건강일지"],
    ["/health-goals/goals", "건강목표"],
    ["/health-reports", "건강리포트"],
    ["/vitals", "바이탈"],
    ["/symptom-check", "증상 체크"],
    ["/reminders", "복약알림"],
    ["/health-insights", "AI 인사이트"],
    ["/chat", "AI 채팅"],
  ] as const;

  const healthActive = healthLinks.some(([href]) => isActive(href));
  const profileImageSrc = user?.profile_image_url
    ? `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}${user.profile_image_url}`
    : null;

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-200 dark:border-zinc-800 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-sm px-4 shadow-sm">
      <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-3 py-4">
        <Link href="/dashboard" className="flex shrink-0 items-center gap-2 font-bold text-blue-700 dark:text-blue-400 text-lg">
          💊 MediGuide AI
        </Link>

        {user && (
          <nav className="flex flex-1 flex-wrap items-center justify-end gap-1">
            <div className="flex flex-wrap items-center gap-1 rounded-lg bg-zinc-50/80 dark:bg-zinc-800/60 p-1">
              {navLink("/dashboard", "대시보드")}
              {navLink("/records", "진료기록")}
              {navLink("/messages", "메시지")}
              {navLink("/appointments", "예약")}
              {user.role === "DOCTOR" && navLink("/health-insights", "문진 요약")}
              {user.role === "PATIENT" && (
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setHealthMenuOpen((open) => !open)}
                    className={`px-3 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
                      healthActive
                        ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                        : "text-zinc-600 hover:bg-zinc-50 dark:text-zinc-400 dark:hover:bg-zinc-800"
                    }`}
                  >
                    건강관리 ▾
                  </button>
                  {healthMenuOpen && (
                    <div className="absolute right-0 top-full mt-2 w-44 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 shadow-lg p-1">
                      {healthLinks.map(([href, label]) => (
                        <Link
                          key={href}
                          href={href}
                          onClick={() => setHealthMenuOpen(false)}
                          className={`block rounded-md px-3 py-2 text-sm transition-colors ${
                            isActive(href)
                              ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                              : "text-zinc-600 hover:bg-zinc-50 dark:text-zinc-300 dark:hover:bg-zinc-800"
                          }`}
                        >
                          {label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {user.role === "DOCTOR" && (
              <Link href="/records/new">
                <Button size="sm" className="ml-2 bg-blue-700 hover:bg-blue-800 h-8 text-xs">
                  + 진료기록 등록
                </Button>
              </Link>
            )}

            <button
              onClick={() => router.push("/notifications")}
              className="relative ml-1 p-2 rounded-md text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
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
                className="ml-1 p-2 rounded-md text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
                aria-label="테마 변경"
              >
                <span className="text-lg">{theme === "dark" ? "☀️" : "🌙"}</span>
              </button>
            )}

            <div className="ml-2 flex items-center gap-3 pl-3 border-l border-zinc-200 dark:border-zinc-700">
              <div className="hidden sm:flex items-center gap-2 rounded-full border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-1.5 shadow-sm">
                {profileImageSrc ? (
                  <img src={profileImageSrc} alt={`${user.name} 프로필`} className="h-8 w-8 rounded-full object-cover" />
                ) : (
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-50 dark:bg-blue-900/40 text-sm font-bold text-blue-700 dark:text-blue-300">
                    {user.role === "DOCTOR" ? "의" : "환"}
                  </div>
                )}
                <div className="text-left">
                  <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 leading-tight">{user.name}</p>
                  <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                    {user.role === "DOCTOR" ? "의사 계정" : "환자 계정"}
                  </p>
                </div>
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
