"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { getUser, logout } from "@/lib/auth";
import type { User } from "@/lib/api";

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setUser(getUser());
  }, []);

  function handleLogout() {
    logout();
    toast.success("로그아웃됐어요.");
    router.push("/login");
  }

  return (
    <header className="sticky top-0 z-50 border-b bg-white/90 backdrop-blur-sm px-6 py-0">
      <div className="max-w-5xl mx-auto flex items-center justify-between h-14">
        <Link href="/records" className="flex items-center gap-2 font-bold text-blue-700 text-lg">
          💊 MediGuide AI
        </Link>

        {user && (
          <nav className="flex items-center gap-1">
            <Link
              href="/records"
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                pathname.startsWith("/records") ? "bg-blue-50 text-blue-700" : "text-zinc-600 hover:bg-zinc-50"
              }`}
            >
              진료 기록
            </Link>

            {user.role === "DOCTOR" && (
              <Link href="/records/new">
                <Button size="sm" className="ml-2 bg-blue-700 hover:bg-blue-800 h-8 text-xs">
                  + 진료기록 등록
                </Button>
              </Link>
            )}

            <div className="ml-4 flex items-center gap-3 pl-4 border-l">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-zinc-800 leading-none">{user.name}</p>
                <p className="text-xs text-zinc-400 mt-0.5">{user.role === "DOCTOR" ? "의사" : "환자"}</p>
              </div>
              <button
                onClick={handleLogout}
                className="text-xs text-zinc-400 hover:text-zinc-700 transition-colors"
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
