"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import Navbar from "@/components/Navbar";
import PaginationBar from "@/components/PaginationBar";
import { messageApi, userApi, Message, PatientSearchResult, DoctorSearchResult, PaginatedResponse } from "@/lib/api";
import { getToken, getUser } from "@/lib/auth";

type Tab = "inbox" | "sent";

export default function MessagesPage() {
  const router = useRouter();
  const user = getUser();

  const [tab, setTab] = useState<Tab>("inbox");
  const [data, setData] = useState<PaginatedResponse<Message> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const [showCompose, setShowCompose] = useState(false);
  const [content, setContent] = useState("");
  const [sending, setSending] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<(PatientSearchResult | DoctorSearchResult)[]>([]);
  const [selectedUser, setSelectedUser] = useState<PatientSearchResult | DoctorSearchResult | null>(null);

  const loadMessages = useCallback(() => {
    setLoading(true);
    const req = tab === "inbox" ? messageApi.inbox(page, 10) : messageApi.sent(page, 10);
    req
      .then(({ data: res }) => setData(res))
      .catch(() => toast.error("메시지를 불러오지 못했어요."))
      .finally(() => setLoading(false));
  }, [tab, page]);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    messageApi.unreadCount().then(({ data: d }) => setUnreadCount(d.unread_count)).catch(() => {});
  }, [router]);

  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  useEffect(() => {
    if (!searchQuery) { setSearchResults([]); return; }
    const t = setTimeout(() => {
      const req = user?.role === "DOCTOR"
        ? userApi.searchPatients(searchQuery)
        : userApi.searchDoctors(searchQuery);
      req.then(({ data: d }) => setSearchResults(d)).catch(() => {});
    }, 300);
    return () => clearTimeout(t);
  }, [searchQuery, user?.role]);

  function resetCompose() {
    setShowCompose(false);
    setContent("");
    setSearchQuery("");
    setSearchResults([]);
    setSelectedUser(null);
  }

  async function handleSend() {
    if (!selectedUser) { toast.error("수신자를 지정해주세요."); return; }
    if (!content.trim()) { toast.error("내용을 입력해주세요."); return; }
    setSending(true);
    try {
      await messageApi.send({ receiver_id: selectedUser.id, content: content.trim() });
      toast.success("메시지를 보냈어요.");
      resetCompose();
      if (tab === "sent") loadMessages();
    } catch {
      toast.error("메시지 전송에 실패했어요.");
    } finally {
      setSending(false);
    }
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString("ko-KR", {
      year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
  }

  const messages = data?.items ?? [];

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">메시지</h1>
            <p className="text-sm text-zinc-500 mt-1">
              미읽은 메시지 <span className="font-semibold text-blue-600">{unreadCount}</span>건
            </p>
          </div>
          <Button onClick={() => setShowCompose(true)} className="bg-blue-700 hover:bg-blue-800">
            + 새 메시지 작성
          </Button>
        </div>

        <div className="flex gap-1 mb-6 border-b border-zinc-200 dark:border-zinc-700">
          {(["inbox", "sent"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => { setTab(t); setPage(1); setExpandedId(null); }}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                tab === t
                  ? "border-blue-600 text-blue-700 dark:text-blue-400"
                  : "border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
              }`}
            >
              {t === "inbox" ? "받은 메시지함" : "보낸 메시지함"}
            </button>
          ))}
        </div>

        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="h-20 rounded-xl bg-zinc-200 dark:bg-zinc-800 animate-pulse" />)}
          </div>
        )}

        {!loading && messages.length === 0 && (
          <div className="text-center py-20 text-zinc-400">
            <p className="text-5xl mb-4">💬</p>
            <p className="text-lg font-medium">메시지가 없어요</p>
          </div>
        )}

        <div className="space-y-3">
          {messages.map((msg) => (
            <div key={msg.id} className="bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 rounded-xl overflow-hidden">
              <button
                className="w-full text-left p-5 hover:bg-zinc-50 dark:hover:bg-zinc-700/50 transition-colors"
                onClick={() => setExpandedId(expandedId === msg.id ? null : msg.id)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {tab === "inbox" && !msg.is_read && (
                        <Badge className="bg-blue-600 text-white text-[10px] px-1.5">NEW</Badge>
                      )}
                      <p className="text-xs text-zinc-400">
                        {tab === "inbox" ? `발신자 #${msg.sender_id}` : `수신자 #${msg.receiver_id}`}
                      </p>
                    </div>
                    <p className="text-sm text-zinc-700 dark:text-zinc-300 truncate">
                      {msg.content.slice(0, 60)}{msg.content.length > 60 ? "…" : ""}
                    </p>
                  </div>
                  <span className="text-xs text-zinc-400 shrink-0">{formatDate(msg.created_at)}</span>
                </div>
              </button>

              {expandedId === msg.id && (
                <div className="px-5 pb-5 border-t border-zinc-50 dark:border-zinc-700">
                  <p className="text-sm text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap pt-4">{msg.content}</p>
                  {msg.record_id && (
                    <p className="text-xs text-zinc-400 mt-3">연관 진료기록 #{msg.record_id}</p>
                  )}
                  {msg.read_at && (
                    <p className="text-xs text-zinc-400 mt-1">읽은 시각: {formatDate(msg.read_at)}</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {data && <PaginationBar page={data.page} pages={data.pages} onPageChange={setPage} />}

        {showCompose && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white dark:bg-zinc-800 rounded-2xl shadow-xl w-full max-w-md p-6">
              <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 mb-4">새 메시지 작성</h2>

              <div className="space-y-4">
                <div>
                  <Label className="mb-1.5">
                    {user?.role === "DOCTOR" ? "환자 검색" : "의사 검색"}
                  </Label>
                  <Input
                    placeholder={user?.role === "DOCTOR" ? "환자 이름 또는 이메일" : "의사 이름 또는 이메일"}
                    value={searchQuery}
                    onChange={(e) => { setSearchQuery(e.target.value); setSelectedUser(null); }}
                    className="dark:bg-zinc-700 dark:border-zinc-600"
                  />
                  {searchResults.length > 0 && !selectedUser && (
                    <ul className="mt-1 border border-zinc-200 dark:border-zinc-600 rounded-lg overflow-hidden">
                      {searchResults.map((p) => (
                        <li key={p.id}>
                          <button
                            className="w-full text-left px-3 py-2 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-700 transition-colors text-zinc-700 dark:text-zinc-300"
                            onClick={() => { setSelectedUser(p); setSearchQuery(p.name); setSearchResults([]); }}
                          >
                            {p.name}{" "}
                            <span className="text-zinc-400 text-xs">({p.email})</span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                  {selectedUser && (
                    <p className="text-xs text-blue-600 mt-1">
                      선택됨: {selectedUser.name} (#{selectedUser.id})
                    </p>
                  )}
                </div>

                <div>
                  <Label className="mb-1.5">내용</Label>
                  <Textarea
                    placeholder="메시지 내용을 입력하세요"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="min-h-28 dark:bg-zinc-700 dark:border-zinc-600"
                  />
                </div>
              </div>

              <div className="flex gap-2 mt-6">
                <Button variant="outline" className="flex-1" onClick={resetCompose}>취소</Button>
                <Button className="flex-1 bg-blue-700 hover:bg-blue-800" onClick={handleSend} disabled={sending}>
                  {sending ? "전송 중…" : "전송"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
