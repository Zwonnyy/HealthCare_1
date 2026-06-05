"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    router.replace(getToken() ? "/dashboard" : "/login");
  }, [router]);
  return (
    <main className="min-h-screen flex items-center justify-center bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <div className="flex flex-col items-center gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-700 text-2xl text-white shadow-lg shadow-blue-700/20 dark:bg-blue-500 dark:shadow-blue-500/10">
          💊
        </div>
        <div className="text-center">
          <p className="text-lg font-bold tracking-tight">MediGuide AI</p>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">화면을 준비하고 있어요.</p>
        </div>
      </div>
    </main>
  );
}
