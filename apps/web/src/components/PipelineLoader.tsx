"use client";

import { useEffect, useState } from "react";

import { ConceptChips } from "./ConceptChips";

const STAGES = [
  { label: "Векторизую запрос", ms: 400 },
  { label: "Ищу в базе мест", ms: 600 },
  { label: "Анализирую совпадения", ms: 700 },
  { label: "Формирую ответ", ms: Infinity },
];

export function PipelineLoader({ query }: { query: string }) {
  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    setActiveStage(0);
    let current = 0;
    const advance = () => {
      const next = current + 1;
      if (next < STAGES.length && STAGES[current].ms !== Infinity) {
        const t = setTimeout(() => {
          current = next;
          setActiveStage(next);
          advance();
        }, STAGES[current].ms);
        return t;
      }
    };
    const t = advance();
    return () => { if (t) clearTimeout(t); };
  }, [query]);

  return (
    <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 min-w-[220px]">
      <div className="space-y-1.5">
        {STAGES.map((stage, i) => {
          const done = i < activeStage;
          const active = i === activeStage;
          return (
            <div key={stage.label} className="flex items-center gap-2">
              <span className="w-4 text-center text-xs">
                {done ? (
                  <span className="text-green-500">✓</span>
                ) : active ? (
                  <span className="text-indigo-500 animate-pulse">◆</span>
                ) : (
                  <span className="text-gray-300">◇</span>
                )}
              </span>
              <span
                className={`text-xs transition-colors duration-300 ${
                  done
                    ? "text-gray-400"
                    : active
                    ? "text-indigo-600 font-medium"
                    : "text-gray-300"
                }`}
              >
                {stage.label}
                {active && (
                  <span className="animate-pulse">...</span>
                )}
              </span>
            </div>
          );
        })}
      </div>
      {activeStage <= 1 && <ConceptChips query={query} />}
    </div>
  );
}
