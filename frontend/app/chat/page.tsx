"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Navbar from "@/components/Navbar";
import { getToken } from "@/lib/auth";

interface ChatMessage {
  role: "user" | "ai";
  content: string;
  loading?: boolean;
}

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "ai", content: "안녕하세요! MediGuide AI입니다. 복약, 증상, 건강 관리에 관해 무엇이든 물어보세요. 😊" },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
  }, [router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const msg = input.trim();
    if (!msg || streaming) return;
    setInput("");

    setMessages((prev) => [
      ...prev,
      { role: "user", content: msg },
      { role: "ai", content: "", loading: true },
    ]);
    setStreaming(true);

    try {
      const token = getToken();
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const response = await fetch(`${baseUrl}/api/v1/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: msg }),
      });

      if (!response.body) throw new Error("No response body");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let aiText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split("\n").filter((l) => l.startsWith("data: "));
        for (const line of lines) {
          try {
            const parsed = JSON.parse(line.slice(6));
            if (parsed.type === "chunk" && parsed.text) {
              aiText += parsed.text;
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = { role: "ai", content: aiText, loading: false };
                return updated;
              });
            }
          } catch {}
        }
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: "ai", content: "응답을 불러오지 못했어요. 다시 시도해주세요.", loading: false };
        return updated;
      });
    } finally {
      setStreaming(false);
    }
  }

  const SUGGESTIONS = ["복약 후 졸린 건 정상인가요?", "두통이 있을 때 어떻게 해야 하나요?", "혈압약과 함께 먹으면 안 되는 음식은?"];

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900 flex flex-col">
      <Navbar />
      <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-6 flex flex-col">
        <div className="mb-4">
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">AI 채팅</h1>
          <p className="text-sm text-zinc-500 mt-1">복약·증상·건강 관리에 대해 AI에게 질문해보세요.</p>
        </div>

        <div className="flex-1 overflow-y-auto space-y-4 mb-4 min-h-0 max-h-[calc(100vh-280px)]">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "ai" && (
                <div className="w-8 h-8 rounded-full bg-blue-700 flex items-center justify-center text-white text-sm mr-2 shrink-0 mt-1">
                  AI
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-blue-700 text-white rounded-tr-sm"
                    : "bg-white dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 border border-zinc-100 dark:border-zinc-700 rounded-tl-sm"
                }`}
              >
                {msg.loading ? (
                  <span className="flex items-center gap-1">
                    <span className="animate-bounce">·</span>
                    <span className="animate-bounce" style={{ animationDelay: "0.1s" }}>·</span>
                    <span className="animate-bounce" style={{ animationDelay: "0.2s" }}>·</span>
                  </span>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {messages.length === 1 && (
          <div className="flex gap-2 flex-wrap mb-3">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => { setInput(s); }}
                className="text-xs px-3 py-1.5 rounded-full border border-blue-200 dark:border-blue-800 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder="메시지를 입력하세요…"
            disabled={streaming}
            className="dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-100"
          />
          <Button onClick={handleSend} disabled={streaming || !input.trim()} className="bg-blue-700 hover:bg-blue-800 shrink-0">
            {streaming ? "…" : "전송"}
          </Button>
        </div>
        <p className="text-xs text-zinc-400 mt-2 text-center">AI 답변은 참고용이며, 실제 의료 결정은 담당 의사와 상담하세요.</p>
      </main>
    </div>
  );
}
