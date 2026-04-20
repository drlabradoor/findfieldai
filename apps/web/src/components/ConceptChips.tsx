"use client";

import { useEffect, useState } from "react";

const STOPWORDS = new Set([
  "для", "как", "что", "где", "или", "это", "мне", "на", "в", "и", "с",
  "по", "из", "до", "от", "за", "при", "над", "под", "без", "между",
  "the", "for", "and", "with", "that", "this", "from", "are", "not",
]);

function extractChips(query: string): string[] {
  return query
    .split(/\s+/)
    .map((w) => w.replace(/[^\wа-яёА-ЯЁa-zA-Z]/g, ""))
    .filter((w) => w.length >= 3 && !STOPWORDS.has(w.toLowerCase()))
    .slice(0, 7);
}

export function ConceptChips({ query }: { query: string }) {
  const chips = extractChips(query);
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    setVisibleCount(0);
  }, [query]);

  useEffect(() => {
    if (visibleCount < chips.length) {
      const t = setTimeout(() => setVisibleCount((v) => v + 1), 160);
      return () => clearTimeout(t);
    }
  }, [visibleCount, chips.length]);

  if (chips.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      <span className="text-xs text-gray-400 self-center">↳</span>
      {chips.map((chip, i) => (
        <span
          key={chip}
          className={`text-xs px-2 py-0.5 rounded-full border transition-all duration-300 ${
            i < visibleCount
              ? "border-indigo-300 bg-indigo-50 text-indigo-600 opacity-100 translate-y-0"
              : "opacity-0 translate-y-1"
          }`}
        >
          {chip}
        </span>
      ))}
    </div>
  );
}
