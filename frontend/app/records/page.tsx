"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Navbar from "@/components/Navbar";
import PaginationBar from "@/components/PaginationBar";
import { recordApi, MedicalRecord, PaginatedResponse } from "@/lib/api";
import { getToken, getUser } from "@/lib/auth";

export default function RecordsPage() {
  const router = useRouter();
  const [user, setUser] = useState<ReturnType<typeof getUser>>(null);
  const [data, setData] = useState<PaginatedResponse<MedicalRecord> | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");

  useEffect(() => {
    setUser(getUser());
  }, []);

  const loadRecords = useCallback(() => {
    if (!getToken()) { router.push("/login"); return; }
    setLoading(true);
    recordApi.list(page, 10, query || undefined)
      .then(({ data: res }) => setData(res))
      .catch(() => toast.error("진료 기록을 불러오지 못했어요."))
      .finally(() => setLoading(false));
  }, [page, query, router]);

  useEffect(() => {
    loadRecords();
  }, [loadRecords]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    setQuery(searchInput.trim());
  }

  const records = data?.items ?? [];

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
              {user?.role === "DOCTOR" ? "작성한 진료 기록" : "내 진료 기록"}
            </h1>
            <p className="text-sm text-zinc-500 mt-1">
              {user?.role === "DOCTOR"
                ? "등록한 진료 기록 목록입니다."
                : "진료 기록을 선택해 AI 가이드를 요청해보세요."}
            </p>
          </div>
          {user?.role === "DOCTOR" && (
            <Link href="/records/new">
              <Button className="bg-blue-700 hover:bg-blue-800">+ 새 진료기록</Button>
            </Link>
          )}
        </div>

        <form onSubmit={handleSearch} className="flex gap-2 mb-6">
          <Input
            placeholder="진단명으로 검색…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-100 dark:placeholder:text-zinc-500"
          />
          <Button type="submit" variant="outline" className="shrink-0 dark:border-zinc-700 dark:text-zinc-300">
            검색
          </Button>
          {query && (
            <Button
              type="button"
              variant="ghost"
              className="shrink-0 text-zinc-500"
              onClick={() => { setSearchInput(""); setQuery(""); setPage(1); }}
            >
              초기화
            </Button>
          )}
        </form>

        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 rounded-xl bg-zinc-200 dark:bg-zinc-800 animate-pulse" />
            ))}
          </div>
        )}

        {!loading && records.length === 0 && (
          <div className="text-center py-20 text-zinc-400">
            <p className="text-5xl mb-4">📋</p>
            <p className="text-lg font-medium">
              {query ? `"${query}" 검색 결과가 없어요` : "진료 기록이 없어요"}
            </p>
            {user?.role === "DOCTOR" && !query && (
              <Link href="/records/new">
                <Button className="mt-4 bg-blue-700 hover:bg-blue-800">첫 진료 기록 등록하기</Button>
              </Link>
            )}
          </div>
        )}

        <div className="space-y-3">
          {records.map((r) => (
            <Link key={r.id} href={`/records/${r.id}`}>
              <div className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 rounded-xl p-5 hover:shadow-md hover:border-blue-100 dark:hover:border-blue-700 transition-all group">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 group-hover:text-blue-700 dark:group-hover:text-blue-400 transition-colors">
                      {r.diagnosis}
                    </h3>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400 line-clamp-1">{r.symptoms}</p>
                  </div>
                  <Badge variant="secondary" className="ml-4 shrink-0 text-xs">
                    {new Date(r.visited_at).toLocaleDateString("ko-KR", { year: "numeric", month: "short", day: "numeric" })}
                  </Badge>
                </div>
                <div className="flex items-center gap-4 mt-3 pt-3 border-t border-zinc-50 dark:border-zinc-700">
                  <span className="text-xs text-zinc-400">
                    💊 처방 약물 {r.prescriptions.length}가지
                  </span>
                  <span className="text-xs text-blue-500 ml-auto group-hover:underline">
                    상세 보기 →
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {data && (
          <PaginationBar page={data.page} pages={data.pages} onPageChange={setPage} />
        )}
      </main>
    </div>
  );
}
