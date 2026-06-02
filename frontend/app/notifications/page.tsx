"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import PaginationBar from "@/components/PaginationBar";
import { notificationApi, Notification, NotificationType, PaginatedResponse } from "@/lib/api";
import { getToken } from "@/lib/auth";

const TYPE_ICON: Record<NotificationType, string> = {
  MESSAGE_RECEIVED: "💬",
  RECORD_CREATED: "📋",
  GUIDE_COMPLETED: "✨",
  ANALYSIS_COMPLETED: "📊",
  APPOINTMENT_REQUESTED: "📅",
  APPOINTMENT_CONFIRMED: "✅",
  MEDICATION_REMINDER: "💊",
};

export default function NotificationsPage() {
  const router = useRouter();
  const [data, setData] = useState<PaginatedResponse<Notification> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [markingAll, setMarkingAll] = useState(false);

  const loadNotifications = useCallback(() => {
    setLoading(true);
    notificationApi
      .list(page, 20)
      .then(({ data: res }) => setData(res))
      .catch(() => toast.error("알림을 불러오지 못했어요."))
      .finally(() => setLoading(false));
  }, [page]);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    loadNotifications();
  }, [router, loadNotifications]);

  async function handleMarkRead(n: Notification) {
    if (n.is_read) return;
    try {
      await notificationApi.markRead(n.id);
      setData((prev) =>
        prev
          ? {
              ...prev,
              items: prev.items.map((item) =>
                item.id === n.id ? { ...item, is_read: true, read_at: new Date().toISOString() } : item
              ),
            }
          : prev
      );
    } catch {
      toast.error("읽음 처리에 실패했어요.");
    }
  }

  async function handleMarkAllRead() {
    setMarkingAll(true);
    try {
      await notificationApi.markAllRead();
      setData((prev) =>
        prev
          ? {
              ...prev,
              items: prev.items.map((item) => ({
                ...item,
                is_read: true,
                read_at: item.read_at ?? new Date().toISOString(),
              })),
            }
          : prev
      );
      toast.success("모두 읽음 처리됐어요.");
    } catch {
      toast.error("처리에 실패했어요.");
    } finally {
      setMarkingAll(false);
    }
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString("ko-KR", {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
  }

  const notifications = data?.items ?? [];
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">알림</h1>
            <p className="text-sm text-zinc-500 mt-1">
              미읽은 알림 <span className="font-semibold text-blue-600">{unreadCount}</span>건
            </p>
          </div>
          {unreadCount > 0 && (
            <Button variant="outline" onClick={handleMarkAllRead} disabled={markingAll} className="dark:border-zinc-700 dark:text-zinc-300">
              {markingAll ? "처리 중…" : "모두 읽음"}
            </Button>
          )}
        </div>

        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="h-20 rounded-xl bg-zinc-200 dark:bg-zinc-800 animate-pulse" />)}
          </div>
        )}

        {!loading && notifications.length === 0 && (
          <div className="text-center py-20 text-zinc-400">
            <p className="text-5xl mb-4">🔔</p>
            <p className="text-lg font-medium">알림이 없어요</p>
          </div>
        )}

        <div className="space-y-2">
          {notifications.map((n) => (
            <button
              key={n.id}
              className={`w-full text-left rounded-xl border transition-all ${
                n.is_read
                  ? "bg-white dark:bg-zinc-800 border-zinc-100 dark:border-zinc-700 hover:border-zinc-200 dark:hover:border-zinc-600"
                  : "bg-blue-50 dark:bg-blue-900/10 border-blue-100 dark:border-blue-800 hover:border-blue-200"
              }`}
              onClick={() => handleMarkRead(n)}
            >
              <div className="flex items-start gap-4 p-4">
                <span className="text-2xl shrink-0 mt-0.5">{TYPE_ICON[n.notification_type]}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className={`text-sm font-medium leading-snug ${n.is_read ? "text-zinc-700 dark:text-zinc-300" : "text-zinc-900 dark:text-zinc-100"}`}>
                      {n.title}
                    </p>
                    <span className="text-xs text-zinc-400 shrink-0">{formatDate(n.created_at)}</span>
                  </div>
                  <p className="text-sm text-zinc-500 mt-0.5 line-clamp-2">{n.body}</p>
                </div>
                {!n.is_read && <span className="shrink-0 mt-1 w-2 h-2 rounded-full bg-blue-500" />}
              </div>
            </button>
          ))}
        </div>

        {data && <PaginationBar page={data.page} pages={data.pages} onPageChange={setPage} />}
      </main>
    </div>
  );
}