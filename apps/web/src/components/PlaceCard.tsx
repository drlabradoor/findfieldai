import type { Place } from "@/lib/api";

export function PlaceCard({
  place,
  score,
}: {
  place: Place;
  score?: number;
}) {
  const cover = place.images?.[0]?.image_url;

  return (
    <article className="min-w-[280px] rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      {cover ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={cover} alt={place.title} className="w-full h-40 object-cover" />
      ) : (
        <div className="w-full h-40 bg-gray-100 flex items-center justify-center text-gray-400">
          no image
        </div>
      )}

      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-base">{place.title}</h3>
          {typeof score === "number" && (
            <span className="shrink-0 text-xs text-indigo-500 font-medium">
              {Math.round(score * 100)}%
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
      </div>
    </article>
  );
}
