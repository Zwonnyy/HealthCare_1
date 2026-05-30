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
import { messageApi, userApi, Message, PatientSearchResult } from "@/lib/api";
import { getToken, getUser } from "@/lib/auth";

type Tab = "inbox" | "sent";

export default function MessagesPage() {
  const router = useRouter();
  const user = getUser();

  const [tab, setTab] = useState<Tab>("inbox");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const [showCompose, setShowCompose] = useState(false);
  const [receiverId, setReceiverId] = useState("");
  const [content, setContent] = useState("");
  const [sending, setSending] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<PatientSearchResult[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<PatientSearchResult | null>(null);

  const loadMessages = useCallback(() => {
    setLoading(true);
    const req = tab === "inbox" ? messageApi.inbox() : messageApi.sent();
    req
      .then(({ data }) => setMessages(data.items))
      .catch(() => toast.error("메시지를 불러오지 못했어요."))
      .finally(() => setLoading(false));
  }, [tab]);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    messageApi.unreadCount().then(({ data }) => setUnreadCount(data.unread_count)).catch(() => {});
  }, [router]);

  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  useEffect(() => {
    if (!searchQuery || user?.role !== "DOCTOR") { setSearchResults([]); return; }
    const t = setTimeout(() => {
      userApi
        .searchPatients(searchQuery)
        .then(({ data }) => setSearchResults(data))
        .catch(() => {});
    }, 300);
    return () => clearTimeout(t);
  }, [searchQuery, user?.role]);

  async function handleSend() {
    const rid = user?.role === "DOCTOR" ? selectedPatient?.id : Number(receiverId);
    if (!rid) { toast.error("수신자를 지정해주세요."); return; }
    if (!content.trim()) { toast.error("내용을 입력해주세요."); return; }
    setSending(true);
    try {
      await messageApi.send({ receiver_id: rid, content: content.trim() });
      toast.success("메시지를 보냈어요.");
      setShowCompose(false);
      setContent("");
      setReceiverId("");
      setSelectedPatient(null);
      setSearchQuery("");
      if (tab === "sent") loadMessages();
    } catch {
      toast.error("메시지 전송에 실패했어요.");
    } finally {
      setSending(false);
    }
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900">메시지</h1>
            <p className="text-sm text-zinc-500 mt-1">
              미읽은 메시지 <span className="font-semibold text-blue-600">{unreadCount}</span>건
            </p>
          </div>
          <Button
            onClick={() => setShowCompose(true)}
            className="bg-blue-700 hover:bg-blue-800"
          >
            + 새 메시지 작성
          </Button>
        </div>

        <div className="flex gap-1 mb-6 border-b border-zinc-200">
          {(["inbox", "sent"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => { setTab(t); setExpandedId(null); }}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                tab === t
                  ? "border-blue-600 text-blue-700"
                  : "border-transparent text-zinc-500 hover:text-zinc-700"
              }`}
            >
              {t === "inbox" ? "받은 메시지함" : "보낸 메시지함"}
            </button>
          ))}
        </div>

        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 rounded-xl bg-zinc-200 animate-pulse" />
            ))}
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
            <div
              key={msg.id}
              className="bg-white border border-zinc-100 rounded-xl overflow-hidden"
            >
              <button
                className="w-full text-left p-5 hover:bg-zinc-50 transition-colors"
                onClick={() => setExpandedId(expandedId === msg.id ? null : msg.id)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {tab === "inbox" && !msg.is_read && (
                        <Badge className="bg-blue-600 text-white text-[10px] px-1.5">NEW</Badge>
                      )}
                      <p className="text-xs text-zinc-400">
                        {tab === "inbox"
                          ? `발신자 #${msg.sender_id}`
                          : `수신자 #${msg.receiver_id}`}
                      </p>
                    </div>
                    <p className="text-sm text-zinc-700 truncate">
                      {msg.content.slice(0, 50)}
                      {msg.content.length > 50 ? "…" : ""}
                    </p>
                  </div>
                  <span className="text-xs text-zinc-400 shrink-0">{formatDate(msg.created_at)}</span>
                </div>
              </button>

              {expandedId === msg.id && (
                <div className="px-5 pb-5 border-t border-zinc-50">
                  <p className="text-sm text-zinc-700 whitespace-pre-wrap pt-4">{msg.content}</p>
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

        {showCompose && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
              <h2 className="text-lg font-bold text-zinc-900 mb-4">새 메시지 작성</h2>

              <div className="space-y-4">
                {user?.role === "DOCTOR" ? (
                  <div>
                    <Label className="mb-1.5">환자 검색</Label>
                    <Input
                      placeholder="환자 이름 또는 이메일"
                      value={searchQuery}
                      onChange={(e) => {
                        setSearchQuery(e.target.value);
                        setSelectedPatient(null);
                      }}
                    />
                    {searchResults.length > 0 && !selectedPatient && (
                      <ul className="mt-1 border border-zinc-200 rounded-lg overflow-hidden">
                        {searchResults.map((p) => (
                          <li key={p.id}>
                            <button
                              className="w-full text-left px-3 py-2 text-sm hover:bg-zinc-50 transition-colors"
                              onClick={() => {
                                setSelectedPatient(p);
                                setSearchQuery(p.name);
                                setSearchResults([]);
                              }}
                            >
                              {p.name}{" "}
                              <span className="text-zinc-400 text-xs">({p.email})</span>
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                    {selectedPatient && (
                      <p className="text-xs text-blue-600 mt-1">
                        선택됨: {selectedPatient.name} (#{selectedPatient.id})
                      </p>
                    )}
                  </div>
                ) : (
                  <div>
                    <Label className="mb-1.5">수신자 ID</Label>
                    <Input
                      type="number"
                      placeholder="의사 ID를 입력하세요"
                      value={receiverId}
                      onChange={(e) => setReceiverId(e.target.value)}
                    />
                  </div>
                )}

                <div>
                  <Label className="mb-1.5">내용</Label>
                  <Textarea
                    placeholder="메시지 내용을 입력하세요"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="min-h-28"
                  />
                </div>
              </div>

              <div className="flex gap-2 mt-6">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowCompose(false);
                    setContent("");
                    setReceiverId("");
                    setSelectedPatient(null);
                    setSearchQuery("");
                    setSearchResults([]);
                  }}
                >
                  취소
                </Button>
                <Button
                  className="flex-1 bg-blue-700 hover:bg-blue-800"
                  onClick={handleSend}
                  disabled={sending}
                >
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