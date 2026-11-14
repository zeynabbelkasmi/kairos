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

interface Props { rec: Recommendation; index: number; onStart: (r: Recommendation) => void }

export default function KairosCard({ rec, index, onStart }: Props) {
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

      <div className="flex flex-1 flex-col px-3 pb-3 pt-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-3 py-1 text-[11px] font-semibold tracking-wider ${TAG_BG[color]}`}>
            {rec.category_tag}
          </span>
          <span className="flex items-center gap-1 text-[11px] font-medium tracking-wider text-muted">
            {rec.maps_url ? <MapPin size={12} /> : <Home size={12} />}
            {rec.location_name}
          </span>
          {rec.lat != null && rec.lon != null && (
            <span className="text-[11px] tracking-wider text-muted">
              · {rec.lat.toFixed(4)}, {rec.lon.toFixed(4)}
            </span>
          )}
        </div>

        <h3 className="mt-4 text-xl font-semibold leading-snug">{rec.title}</h3>
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
      </div>
    </motion.article>
  );
}
