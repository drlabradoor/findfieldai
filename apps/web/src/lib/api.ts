const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type PlaceImage = { id: string; image_url: string; sort_order: number };

export type Place = {
  id: string;
  title: string;
  short_description: string;
  long_description: string;
  country: string;
  city: string;
  category: string;
  tags: string[];
  budget_level: string;
  indoor_outdoor: string;
  images: PlaceImage[];
};

export type SearchHit = { score: number; place: Place; match_reason?: string | null };

export type SearchResponse = {
  query: string | null;
  count: number;
  hits: SearchHit[];
};

export type PlaceFilters = {
  country?: string;
  city?: string;
  category?: string;
  budget_level?: string;
  indoor_outdoor?: string;
  tags?: string[];
};

export async function searchText(
  query: string,
  filters: PlaceFilters = {},
  limit = 12,
): Promise<SearchResponse> {
  const res = await fetch(`${BASE}/search/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, filters, limit }),
  });
  if (!res.ok) throw new Error(`search failed: ${res.status}`);
  return res.json();
}

export async function searchImage(
  file: File,
  filters: PlaceFilters = {},
  limit = 12,
): Promise<SearchResponse> {
  const form = new FormData();
  form.append("image", file);
  form.append("filters", JSON.stringify(filters));
  form.append("limit", String(limit));
  const res = await fetch(`${BASE}/search/image`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`image search failed: ${res.status}`);
  return res.json();
}

export type ChatRole = "user" | "assistant" | "system";
export type ChatMessage = { role: ChatRole; content: string };

export type ChatQueryResponse = {
  answer: string;
  follow_up_question: string | null;
  concepts: string[];
  results: SearchHit[];
};

export async function chatQuery(
  message: string,
  history: ChatMessage[] = [],
): Promise<ChatQueryResponse> {
  const res = await fetch(`${BASE}/chat/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) throw new Error(`chat failed: ${res.status}`);
  return res.json();
}
