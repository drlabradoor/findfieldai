"use client";

import { useState } from "react";

import { PlaceCard } from "@/components/PlaceCard";
import { searchText, type SearchHit } from "@/lib/api";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hits, setHits] = useState<SearchHit[]>([]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await searchText(query);
      setHits(res.hits);
    } catch (err) {
      setError(err instanceof Error ? err.message : "search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-bold mb-2">Findfield AI</h1>
      <p className="text-gray-600 mb-6">
        Discover tourist places by text, image, or chat — results come from a
        real vector index, not invented by the model.
      </p>

      <form onSubmit={onSubmit} className="flex gap-2 mb-8">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="quiet coastal town near a city"
          className="flex-1 px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2 rounded-lg bg-gray-900 text-white disabled:opacity-50"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {error && <p className="text-red-600 mb-4">{error}</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {hits.map((h) => (
          <PlaceCard key={h.place.id} place={h.place} score={h.score} />
        ))}
      </div>

      {!loading && hits.length === 0 && (
        <p className="text-gray-500">Try a search to see results.</p>
      )}
    </main>
  );
}
