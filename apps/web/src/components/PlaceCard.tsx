"use client";

import { useEffect, useState } from "react";

import type { Place } from "@/lib/api";

export function PlaceCard({
  place,
  score,
  matchReason,
}: {
  place: Place;
  score?: number;
  matchReason?: string | null;
}) {
  const [barWidth, setBarWidth] = useState(0);

  useEffect(() => {
    if (typeof score !== "number") return;
    const t = setTimeout(() => setBarWidth(Math.round(score * 100)), 120);
    return () => clearTimeout(t);
  }, [score]);

  const cover = place.images?.[0]?.image_url;

  return (
    <article className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      {cover ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={cover} alt={place.title} className="w-full h-40 object-cover" />
      ) : (
        <div className="w-full h-40 bg-gray-100 flex items-center justify-center text-gray-400">
          no image
        </div>
      )}

      {typeof score === "number" && (
        <div className="relative h-1 bg-gray-100">
          <div
            className="absolute inset-y-0 left-0 bg-indigo-400 transition-all duration-700 ease-out"
            style={{ width: `${barWidth}%` }}
          />
        </div>
      )}

      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-base">{place.title}</h3>
          {typeof score === "number" && (
            <span className="shrink-0 text-xs text-indigo-500 font-medium">
              {barWidth}%
            </span>
          )}
        </div>
        <p className="text-sm text-gray-600">
          {place.city}, {place.country}
        </p>
        <p className="text-sm mt-2 line-clamp-3">{place.short_description}</p>
        <div className="flex flex-wrap gap-1 mt-3">
          {place.tags?.slice(0, 4).map((t) => (
            <span
              key={t}
              className="text-xs px-2 py-0.5 bg-gray-100 rounded-full text-gray-700"
            >
              {t}
            </span>
          ))}
        </div>
        {matchReason && (
          <details className="mt-3">
            <summary className="text-xs text-gray-400 cursor-pointer select-none hover:text-gray-600">
              ✦ Почему это место?
            </summary>
            <p className="text-xs text-gray-600 mt-1 leading-relaxed">{matchReason}</p>
          </details>
        )}
      </div>
    </article>
  );
}
