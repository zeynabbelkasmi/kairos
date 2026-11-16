import { useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import type { RecommendRequest } from "../types";

const MOODS = ["Fatigué(e)", "Créatif(ve)", "En quête de calme", "Plein d'énergie"];

interface Props { initial?: RecommendRequest | null; onSubmit: (req: RecommendRequest) => void }

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={`flex items-center gap-2 rounded-full border-2 px-4 py-2 text-sm font-semibold transition-colors ${
        active ? "border-sun bg-sun text-ink" : "border-line bg-transparent text-ink hover:border-sun"
      }`}
    >
      {children}
    </button>
  );
}

function Group({ legend, children }: { legend: string; children: ReactNode }) {
  return (
    <fieldset className="mt-7">
      <legend className="text-sm font-bold text-ink">{legend}</legend>
      <div className="mt-3 flex flex-wrap gap-2">{children}</div>
    </fieldset>
  );
}

export default function KairosForm({ initial, onSubmit }: Props) {
  const [text, setText] = useState(initial?.user_input ?? "");
  const [mood, setMood] = useState<string | null>(initial?.mood ?? null);

  const canSubmit = text.trim().length > 0 || mood !== null;

  return (
    <motion.form
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      onSubmit={(e) => {
        e.preventDefault();
        if (canSubmit) onSubmit({ user_input: text.trim(), mood, max_options: 3 });
      }}
      className="mx-auto w-full max-w-2xl rounded-3xl bg-surface p-6 shadow-soft sm:p-10"
    >
      <label htmlFor="prompt" className="block text-2xl font-extrabold leading-snug text-ink">
        Comment te sens-tu, et de quoi as-tu envie&nbsp;?
      </label>
      <textarea
        id="prompt"
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={3}
        placeholder="Je suis saturée d'écrans, j'ai besoin de prendre l'air…"
        className="mt-5 w-full resize-none rounded-xl border border-line bg-blush/50 p-4 text-[15px] leading-relaxed text-ink placeholder:text-muted/80 focus:border-coral focus:outline-none"
      />

      <Group legend="Ton énergie du moment">
        {MOODS.map((m) => (
          <Chip key={m} active={mood === m} onClick={() => setMood(mood === m ? null : m)}>{m}</Chip>
        ))}
      </Group>

      <button
        type="submit"
        disabled={!canSubmit}
        className="mt-10 w-full rounded-full bg-coral-deep px-6 py-4 text-[15px] font-bold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-35"
      >
        Me proposer trois idées
      </button>
      {!canSubmit && <p className="mt-3 text-center text-[13px] text-muted">Écris quelques mots ou choisis une énergie pour commencer.</p>}
    </motion.form>
  );
}
