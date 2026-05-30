"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import { notificationApi, Notification, NotificationType } from "@/lib/api";
import { getToken } from "@/lib/auth";

const TYPE_ICON: Record<NotificationType, string> = {
  MESSAGE_RECEIVED: "💬",
  RECORD_CREATED: "📋",
  GUIDE_COMPLETED: "✨",
  ANALYSIS_COMPLETED: "📊",
};

export default function NotificationsPage() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [markingAll, setMarkingAll] = useState(false);

  const loadNotifications = useCallback(() => {
    setLoading(true);
    notificationApi
      .list()
      .then(({ data }) => setNotifications(data.items))
      .catch(() => toast.error("알림을 불러오지 못했어요."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    loadNotifications();
  }, [router, loadNotifications]);

  async function handleMarkRead(n: Notification) {
    if (n.is_read) return;
    try {
      await notificationApi.markRead(n.id);
      setNotifications((prev) =>
        prev.map((item) =>
          item.id === n.id
            ? { ...item, is_read: true, read_at: new Date().toISOString() }
            : item
        )
      );
    } catch {
      toast.error("읽음 처리에 실패했어요.");
    }
  }

  async function handleMarkAllRead() {
    setMarkingAll(true);
    try {
      await notificationApi.markAllRead();
      setNotifications((prev) =>
        prev.map((item) => ({ ...item, is_read: true, read_at: item.read_at ?? new Date().toISOString() }))
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
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="min-h-screen bg-zinc-50">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900">알림</h1>
            <p className="text-sm text-zinc-500 mt-1">
              미읽은 알림 <span className="font-semibold text-blue-600">{unreadCount}</span>건
            </p>
          </div>
          {unreadCount > 0 && (
            <Button
              variant="outline"
              onClick={handleMarkAllRead}
              disabled={markingAll}
            >
              {markingAll ? "처리 중…" : "모두 읽음"}
            </Button>
          )}
        </div>

        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 rounded-xl bg-zinc-200 animate-pulse" />
            ))}
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
                  ? "bg-white border-zinc-100 hover:border-zinc-200"
                  : "bg-blue-50 border-blue-100 hover:border-blue-200"
              }`}
              onClick={() => handleMarkRead(n)}
            >
              <div className="flex items-start gap-4 p-4">
                <span className="text-2xl shrink-0 mt-0.5">{TYPE_ICON[n.notification_type]}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className={`text-sm font-medium leading-snug ${n.is_read ? "text-zinc-700" : "text-zinc-900"}`}>
                      {n.title}
                    </p>
                    <span className="text-xs text-zinc-400 shrink-0">{formatDate(n.created_at)}</span>
                  </div>
                  <p className="text-sm text-zinc-500 mt-0.5 line-clamp-2">{n.body}</p>
                </div>
                {!n.is_read && (
                  <span className="shrink-0 mt-1 w-2 h-2 rounded-full bg-blue-500" />
                )}
              </div>
            </button>
          ))}
        </div>
      </main>
    </div>
  );
}
