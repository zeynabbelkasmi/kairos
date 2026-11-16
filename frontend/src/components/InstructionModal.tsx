import { motion } from "framer-motion";
import { X } from "lucide-react";
import type { Recommendation } from "../types";

interface Props { rec: Recommendation; onClose: () => void }

export default function InstructionModal({ rec, onClose }: Props) {
  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center bg-charcoal/20 p-4 backdrop-blur-sm"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        role="dialog"
        aria-modal="true"
        aria-label={rec.title}
        className="w-full max-w-md rounded-3xl bg-surface p-8 shadow-xl"
        initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 30, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-6 flex items-start justify-between gap-4">
          <h3 className="text-2xl font-extrabold leading-snug text-ink">{rec.title}</h3>
          <button onClick={onClose} aria-label="Fermer" className="rounded-full p-1 text-muted hover:bg-card">
            <X size={20} />
          </button>
        </div>
        <ol className="space-y-4">
          {(rec.instructions ?? []).map((step, i) => (
            <motion.li
              key={i}
              className="flex gap-4"
              initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 + i * 0.12 }}
            >
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sun text-sm font-bold text-ink">
                {i + 1}
              </span>
              <span className="pt-0.5 text-[15px] leading-relaxed text-charcoal">{step}</span>
            </motion.li>
          ))}
        </ol>
        <p className="mt-8 text-center font-script text-2xl font-bold text-coral-deep">Pose ton téléphone. Ce moment t'appartient.</p>
      </motion.div>
    </motion.div>
  );
}
