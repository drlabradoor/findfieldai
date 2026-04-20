"use client";

import { useEffect, useRef, useState } from "react";

import { PipelineLoader } from "@/components/PipelineLoader";
import { PlaceCard } from "@/components/PlaceCard";
import {
  chatQuery,
  type ChatMessage,
  type SearchHit,
} from "@/lib/api";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  displayedContent?: string;
  results?: SearchHit[];
  userQuery?: string;
  stage3Reached?: boolean;
};

const SUGGESTIONS = [
  "Тихий прибрежный город рядом с мегаполисом",
  "Детский музей в Европе",
  "Места для дождливого дня в Лиссабоне",
];

const STAGE_3_DELAY_MS = 4300;

let nextId = 1;

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const target = messages.find(
      (m) =>
        m.role === "assistant" &&
        m.stage3Reached &&
        !!m.content &&
        (m.displayedContent?.length ?? 0) < m.content.length,
    );
    if (!target) return;

    const timer = setTimeout(() => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === target.id
            ? {
                ...msg,
                displayedContent: target.content.slice(
                  0,
                  (target.displayedContent?.length ?? 0) + 1,
                ),
              }
            : msg,
        ),
      );
    }, 30);

    return () => clearTimeout(timer);
  }, [messages]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = { id: nextId++, role: "user", content: trimmed };
    const assistantId = nextId++;
    const assistantMsg: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      displayedContent: "",
      userQuery: trimmed,
      stage3Reached: false,
    };

    const history: ChatMessage[] = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput("");
    setLoading(true);
    setError(null);

    setTimeout(() => {
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, stage3Reached: true } : m)),
      );
    }, STAGE_3_DELAY_MS);

    try {
      const res = await chatQuery(trimmed, history);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: res.answer, results: res.results }
            : m,
        ),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Что-то пошло не так");
      setMessages((prev) => prev.filter((m) => m.id !== assistantId));
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    send(input);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  }

  return (
    <div className="flex flex-col min-h-screen max-w-3xl mx-auto px-4">
      {/* Header */}
      <header className="py-4 border-b border-gray-200">
        <h1 className="text-xl font-semibold">Findfield AI</h1>
        <p className="text-sm text-gray-500">
          Туристические места — результаты из реального индекса, не выдуманные
        </p>
      </header>

      {/* Messages */}
      <main className="flex-1 py-6 space-y-6 overflow-y-auto">
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center gap-4 mt-16 text-center">
            <p className="text-gray-500 text-sm">Спросите о местах для путешествий</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="px-3 py-1.5 text-sm rounded-full border border-gray-300 hover:bg-gray-100 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => {
          if (m.role === "user") {
            return (
              <div key={m.id} className="flex justify-end">
                <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-gray-900 text-white">
                  <p className="text-sm whitespace-pre-wrap">{m.content}</p>
                </div>
              </div>
            );
          }

          const isReady = !!(m.stage3Reached && m.content);
          const isComplete =
            isReady && (m.displayedContent?.length ?? 0) >= m.content.length;

          return (
            <div key={m.id} className="flex justify-start">
              <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-white border border-gray-200 text-gray-900 space-y-3">
                <PipelineLoader query={m.userQuery || ""} isComplete={isComplete} />

                {isReady ? (
                  <p className="text-sm whitespace-pre-wrap">{m.displayedContent}</p>
                ) : (
                  <div className="space-y-2 animate-pulse">
                    <div className="h-3 bg-gray-100 rounded w-3/4" />
                    <div className="h-3 bg-gray-100 rounded w-1/2" />
                    <div className="h-3 bg-gray-100 rounded w-5/6" />
                  </div>
                )}

                {isReady && m.results && m.results.length > 0 && (
                  <div className="-mx-4 px-4 flex gap-3 overflow-x-auto snap-x snap-mandatory pb-2 scrollbar-thin">
                    {m.results.map((h) => (
                      <PlaceCard
                        key={h.place.id}
                        place={h.place}
                        score={h.score}
                        matchReason={h.match_reason}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {error && <p className="text-center text-sm text-red-500">{error}</p>}

        <div ref={bottomRef} />
      </main>

      {/* Input */}
      <footer className="sticky bottom-0 pb-4 pt-2 bg-gray-50">
        <form onSubmit={onSubmit} className="flex gap-2 items-end">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Спросите о месте…"
            rows={1}
            disabled={loading}
            className="flex-1 resize-none px-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400 text-sm disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2.5 rounded-xl bg-gray-900 text-white text-sm disabled:opacity-40"
          >
            {loading ? "…" : "Отправить"}
          </button>
        </form>
        <p className="text-xs text-gray-400 mt-1 pl-1">Enter — отправить, Shift+Enter — перенос</p>
      </footer>
    </div>
  );
}
