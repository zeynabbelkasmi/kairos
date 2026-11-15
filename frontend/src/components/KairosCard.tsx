import { useState } from "react";
import { motion } from "framer-motion";
import { MapPin, Home, Play, ExternalLink, Trees, Palette, BookOpen } from "lucide-react";
import type { Recommendation, TagColor } from "../types";

const TAG_BG: Record<TagColor, string> = {
  sauge: "bg-accent-sauge",
  peche: "bg-accent-peche",
  lilas: "bg-accent-lilas",
};
const FALLBACK_GRADIENT: Record<TagColor, string> = {
  sauge: "from-accent-sauge to-card",
  peche: "from-accent-peche to-card",
  lilas: "from-accent-lilas to-card",
};

const ICON: Record<TagColor, typeof Trees> = { sauge: Trees, peche: Palette, lilas: BookOpen };

interface Props { rec: Recommendation; index: number; onStart: (r: Recommendation) => void; onDone: (r: Recommendation) => void }

export default function KairosCard({ rec, index, onStart, onDone }: Props) {
  const [imgError, setImgError] = useState(false);
  const color: TagColor = rec.tag_color in TAG_BG ? rec.tag_color : "sauge";

  return (
    <motion.article
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.15, duration: 0.6, ease: "easeOut" }}
      className="flex flex-col overflow-hidden rounded-4xl bg-card p-3"
    >
      <div className="aspect-[4/3] overflow-hidden rounded-3xl">
        {imgError || !rec.image_url ? (
          <div className={`flex h-full w-full items-center justify-center bg-gradient-to-br ${FALLBACK_GRADIENT[color]}`}>
            {(() => { const Icon = ICON[color]; return <Icon size={56} strokeWidth={1.25} className="text-charcoal/50" />; })()}
          </div>
        ) : (
          <img
            src={rec.image_url}
            alt={rec.title}
            loading="lazy"
            onError={() => setImgError(true)}
            className="h-full w-full object-cover transition-transform duration-700 hover:scale-105"
          />
        )}
      </div>

      {rec.is_place && (
        <div className="flex flex-wrap items-center justify-between gap-1 px-2 pt-2 text-[11px] text-muted">
          <span>Google Maps</span>
          <a href={rec.photo_google_maps_uri || rec.maps_url || "#"} target="_blank" rel="noopener noreferrer" className="underline">Voir la photo sur Maps</a>
          {rec.photo_author && (rec.photo_author_url ? (
            <a href={rec.photo_author_url} target="_blank" rel="noopener noreferrer" className="underline">Photo : {rec.photo_author}</a>
          ) : <span>Photo : {rec.photo_author}</span>)}
        </div>
      )}
      <div className="flex flex-1 flex-col px-3 pb-3 pt-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-3 py-1 text-[11px] font-semibold tracking-wider ${TAG_BG[color]}`}>{rec.category_tag}</span>
          <span className="flex items-center gap-1 text-[11px] font-medium tracking-wider text-muted">{rec.maps_url ? <MapPin size={12} /> : <Home size={12} />}{rec.location_name}</span>
        </div>

        <h3 className="mt-4 text-xl font-semibold leading-snug">{rec.title}</h3>
        {rec.rating != null && <p className="mt-1 text-sm font-medium text-charcoal">★ {rec.rating.toFixed(1)} <span className="font-normal text-muted">({rec.user_rating_count ?? 0} avis Google)</span></p>}
        <p className="mt-2 flex-1 text-[15px] leading-relaxed text-muted">{rec.description}</p>

        {rec.maps_url ? (
          <a
            href={rec.maps_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-6 flex items-center justify-center gap-2 rounded-full bg-canvas px-5 py-3 text-sm font-medium transition hover:bg-white"
          >
            Ouvrir dans Google Maps <ExternalLink size={15} />
          </a>
        ) : (
          <button
            onClick={() => onStart(rec)}
            className="mt-6 flex items-center justify-center gap-2 rounded-full bg-canvas px-5 py-3 text-sm font-medium transition hover:bg-white"
          >
            <Play size={15} /> Lancer la consigne
          </button>
        )}
        {!rec.is_place && <button onClick={() => onDone(rec)} className="mt-2 rounded-full px-5 py-2 text-xs text-muted hover:bg-accent-sauge">
          Marquer comme faite
        </button>}
      </div>
    </motion.article>
  );
}
