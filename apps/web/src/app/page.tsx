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
  results?: SearchHit[];
};

const SUGGESTIONS = [
  "Тихий прибрежный город рядом с мегаполисом",
  "Детский музей в Европе",
  "Места для дождливого дня в Лиссабоне",
];

let nextId = 1;

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastQuery, setLastQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = { id: nextId++, role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLastQuery(trimmed);
    setLoading(true);
    setError(null);

    const history: ChatMessage[] = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const res = await chatQuery(trimmed, history);
      const assistantMsg: Message = {
        id: nextId++,
        role: "assistant",
        content: res.answer,
        results: res.results,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Что-то пошло не так");
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

        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                m.role === "user"
                  ? "bg-gray-900 text-white"
                  : "bg-white border border-gray-200 text-gray-900"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{m.content}</p>
              {m.results && m.results.length > 0 && (
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {m.results.map((h) => (
                    <PlaceCard key={h.place.id} place={h.place} score={h.score} matchReason={h.match_reason} />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <PipelineLoader query={lastQuery} />
          </div>
        )}

        {error && (
          <p className="text-center text-sm text-red-500">{error}</p>
        )}

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
