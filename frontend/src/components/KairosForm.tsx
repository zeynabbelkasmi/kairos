import { useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import { MapPin, Sparkles, User, Users } from "lucide-react";
import type { RecommendRequest } from "../types";

const MOODS = ["Fatigué(e)", "Créatif(ve)", "En quête de calme", "Plein d'énergie"];
// Distance maximale des lieux proposés, en mètres (le backend accepte 300 à 10 000).
const RADII = [500, 1000, 2000, 5000, 10000];

export function formatRadius(m: number) {
  return m < 1000 ? `${m} m` : `${m / 1000} km`;
}

interface Props { initial?: RecommendRequest | null; onSubmit: (req: RecommendRequest) => void }

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm transition ${
        active ? "bg-charcoal text-canvas" : "bg-canvas text-charcoal hover:bg-white"
      }`}
    >
      {children}
    </button>
  );
}

export default function KairosForm({ initial, onSubmit }: Props) {
  const [text, setText] = useState(initial?.user_input ?? "");
  const [mood, setMood] = useState<string | null>(initial?.mood ?? null);
  const [alone, setAlone] = useState(initial?.is_alone ?? true);
  const [radius, setRadius] = useState(initial?.radius ?? 2000);

  const canSubmit = text.trim().length > 0 || mood !== null;

  return (
    <motion.form
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5 }}
      onSubmit={(e) => {
        e.preventDefault();
        if (canSubmit) onSubmit({ user_input: text.trim(), mood, is_alone: alone, max_options: 3, radius });
      }}
      className="mx-auto w-full max-w-2xl rounded-4xl bg-card p-6 sm:p-10"
    >
      <label htmlFor="prompt" className="block text-lg font-medium">
        Comment te sens-tu ou qu'as-tu envie de faire ?
      </label>
      <textarea
        id="prompt"
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={3}
        placeholder="Ex : Je suis saturée d'écrans et j'ai besoin de prendre l'air…"
        className="mt-4 w-full resize-none rounded-3xl bg-canvas p-5 text-[15px] leading-relaxed placeholder:text-muted/70 focus:outline-none focus:ring-2 focus:ring-accent-lilas"
      />

      <p className="mt-6 text-xs font-semibold tracking-wider text-muted">HUMEUR / ÉNERGIE</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {MOODS.map((m) => (
          <Chip key={m} active={mood === m} onClick={() => setMood(mood === m ? null : m)}>{m}</Chip>
        ))}
      </div>

      <p className="mt-6 text-xs font-semibold tracking-wider text-muted">CONTEXTE SOCIAL</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Chip active={alone} onClick={() => setAlone(true)}><User size={15} /> Seul(e)</Chip>
        <Chip active={!alone} onClick={() => setAlone(false)}><Users size={15} /> Accompagné(e)</Chip>
      </div>

      <p className="mt-6 text-xs font-semibold tracking-wider text-muted">DISTANCE MAXIMALE</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {RADII.map((r) => (
          <Chip key={r} active={radius === r} onClick={() => setRadius(r)}>
            {r === radius && <MapPin size={15} />} {formatRadius(r)}
          </Chip>
        ))}
      </div>

      <button
        type="submit"
        disabled={!canSubmit}
        className="mt-10 flex w-full items-center justify-center gap-2 rounded-full bg-charcoal px-6 py-4 text-[15px] font-medium text-canvas transition hover:bg-charcoal/90 disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Sparkles size={17} /> Trouver un moment Kairos
      </button>
    </motion.form>
  );
}
