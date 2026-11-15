import { useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { MapPin, Play, ExternalLink, Trees, Palette, BookOpen, Check, Star } from "lucide-react";
import type { Recommendation, TagColor } from "../types";

// Chaque catégorie a sa teinte : bande latérale, icône, étiquette.
const CATEGORY: Record<TagColor, { hue: string; tint: string; Icon: typeof Trees }> = {
  sauge: { hue: "#5F7D5A", tint: "#DCE5D6", Icon: Trees },
  peche: { hue: "#A86A28", tint: "#EFE0C9", Icon: Palette },
  lilas: { hue: "#6E6388", tint: "#E3DCEC", Icon: BookOpen },
};

const sentenceCase = (s: string) => (s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : s);
const formatDistance = (m: number) =>
  m < 1000 ? `${m} m` : `${(m / 1000).toFixed(1).replace(".", ",")} km`;

interface Props { rec: Recommendation; index: number; onStart: (r: Recommendation) => void; onDone: (r: Recommendation) => void }

export default function KairosCard({ rec, index, onStart, onDone }: Props) {
  const [imgError, setImgError] = useState(false);
  const reduceMotion = useReducedMotion();
  const color: TagColor = rec.tag_color in CATEGORY ? rec.tag_color : "sauge";
  const { hue, tint, Icon } = CATEGORY[color];
  const TagIcon = rec.is_place ? MapPin : Icon;
  // Google préfixe souvent l'adresse par le nom du lieu : on ne le répète pas.
  const address = rec.location_name.startsWith(`${rec.title}, `)
    ? rec.location_name.slice(rec.title.length + 2)
    : rec.location_name;
  const hours = rec.opening_hours ?? "";
  const isOpen = /^ouvert/i.test(hours);

  return (
    <motion.article
      initial={reduceMotion ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5, ease: "easeOut" }}
      className="relative flex flex-col overflow-hidden rounded-xl bg-surface"
    >
      <span aria-hidden className="absolute inset-y-0 left-0 w-1" style={{ backgroundColor: hue }} />

      {rec.is_place && (
        <div className="aspect-[5/4] overflow-hidden">
          {imgError || !rec.image_url ? (
            <div className="flex h-full w-full items-center justify-center" style={{ backgroundColor: tint }}>
              <Icon size={44} strokeWidth={1.25} style={{ color: hue }} />
            </div>
          ) : (
            <img
              src={rec.image_url}
              alt={rec.title}
              loading="lazy"
              onError={() => setImgError(true)}
              className="h-full w-full object-cover"
            />
          )}
        </div>
      )}

      <div className="flex flex-1 flex-col p-6 pl-7">
        <p className="inline-flex items-center gap-1.5 text-[13px] font-medium" style={{ color: hue }}>
          <TagIcon size={14} strokeWidth={2} /> {sentenceCase(rec.category_tag)}
        </p>

        <h3 className="mt-3 font-serif text-[1.4rem] font-medium leading-tight text-ink">{rec.title}</h3>

        {rec.is_place ? (
          <div className="mt-3 space-y-1.5 text-sm text-muted">
            {rec.rating != null && (
              <p className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <span className="inline-flex items-center gap-1 font-semibold text-ink">
                  <Star size={14} fill={hue} stroke={hue} /> {rec.rating.toFixed(1).replace(".", ",")}
                </span>
                <span>{rec.user_rating_count ?? 0} avis</span>
                {rec.distance_m != null && (
                  <span className="inline-flex items-center gap-1"><MapPin size={13} /> à {formatDistance(rec.distance_m)}</span>
                )}
              </p>
            )}
            {hours && <p className={isOpen ? "font-medium" : ""} style={isOpen ? { color: hue } : undefined}>{hours}</p>}
            {address && <p className="leading-snug">{address}</p>}
          </div>
        ) : (
          <p className="mt-3 text-[15px] leading-relaxed text-muted">{rec.description}</p>
        )}

        <div className="mt-auto pt-6">
          {rec.maps_url ? (
            <a
              href={rec.maps_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 rounded-full bg-ink px-5 py-3 text-sm font-medium text-paper transition-opacity hover:opacity-90"
            >
              Ouvrir dans Google Maps <ExternalLink size={15} />
            </a>
          ) : (
            <button
              onClick={() => onStart(rec)}
              className="flex w-full items-center justify-center gap-2 rounded-full bg-ink px-5 py-3 text-sm font-medium text-paper transition-opacity hover:opacity-90"
            >
              <Play size={15} /> Voir les étapes
            </button>
          )}
          {!rec.is_place && (
            <button
              onClick={() => onDone(rec)}
              className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-full py-2 text-[13px] text-muted transition-colors hover:text-ink"
            >
              <Check size={14} /> Marquer comme faite
            </button>
          )}
        </div>

        {rec.is_place && (
          <p className="mt-4 text-[11px] text-muted">
            Lieu et photo : <a href={rec.photo_google_maps_uri || rec.maps_url || "#"} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2">Google Maps</a>
            {rec.photo_author && (
              <>, photo de {rec.photo_author_url
                ? <a href={rec.photo_author_url} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2">{rec.photo_author}</a>
                : rec.photo_author}</>
            )}
          </p>
        )}
      </div>
    </motion.article>
  );
}
