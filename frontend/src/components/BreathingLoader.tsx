import { motion } from "framer-motion";

export default function BreathingLoader() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col items-center justify-center gap-10 py-24"
    >
      <div className="relative h-48 w-48">
        <motion.div
          className="absolute inset-0 rounded-full blur-2xl"
          animate={{ scale: [0.8, 1.15, 0.8], backgroundColor: ["#D2E0D9", "#E0D8EA", "#D2E0D9"] }}
          transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute inset-8 rounded-full blur-md opacity-80"
          animate={{ scale: [0.9, 1.05, 0.9], backgroundColor: ["#E0D8EA", "#D2E0D9", "#E0D8EA"] }}
          transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>
      <div className="text-center">
        <motion.p
          className="text-lg text-charcoal"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 5, repeat: Infinity }}
        >
          Inspire… expire…
        </motion.p>
        <p className="mt-2 text-sm text-muted">Sélection des meilleures options pour toi…</p>
      </div>
    </motion.div>
  );
}
