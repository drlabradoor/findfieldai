"use client";

import { useEffect, useState } from "react";

import { ConceptChips } from "./ConceptChips";

const STAGES = ["Векторизую запрос", "Ищу в базе мест", "Анализирую совпадения", "Формирую ответ"];
const STAGE_DURATIONS_MS = [1000, 1500, 1800];

export function PipelineLoader({
  query,
  isComplete,
}: {
  query: string;
  isComplete: boolean;
}) {
  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    setActiveStage(0);
    const timers: ReturnType<typeof setTimeout>[] = [];
    let cumulative = 0;
    STAGE_DURATIONS_MS.forEach((ms, i) => {
      cumulative += ms;
      timers.push(setTimeout(() => setActiveStage(i + 1), cumulative));
    });
    return () => timers.forEach(clearTimeout);
  }, [query]);

  useEffect(() => {
    if (isComplete) {
      setActiveStage((s) => Math.max(s, STAGES.length));
    }
  }, [isComplete]);

  return (
    <div className="min-w-[220px]">
      <div className="space-y-1.5">
        {STAGES.map((label, i) => {
          const done = i < activeStage;
          const active = i === activeStage;
          return (
            <div key={label} className="flex items-center gap-2">
              <span className="w-4 text-center text-xs">
                {done ? (
                  <span className="text-gray-400">✓</span>
                ) : active ? (
                  <span className="text-gray-500 animate-pulse">◆</span>
                ) : (
                  <span className="text-gray-300">◇</span>
                )}
              </span>
              <span
                className={`text-xs transition-colors duration-300 ${
                  done
                    ? "text-gray-500"
                    : active
                    ? "text-gray-600 font-medium"
                    : "text-gray-400"
                }`}
              >
                {label}
                {active && <span className="animate-pulse">...</span>}
              </span>
            </div>
          );
        })}
      </div>
      {activeStage <= 1 && <ConceptChips query={query} />}
    </div>
  );
}
