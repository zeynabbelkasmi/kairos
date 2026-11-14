import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, RefreshCw, MapPinOff } from "lucide-react";
import KairosForm from "./components/KairosForm";
import BreathingLoader from "./components/BreathingLoader";
import KairosCard from "./components/KairosCard";
import InstructionModal from "./components/InstructionModal";
import { fetchRecommendations } from "./api";
import type { Recommendation, RecommendRequest } from "./types";

type Phase = "form" | "loading" | "results";

export default function App() {
  const [phase, setPhase] = useState<Phase>("form");
  const [lastReq, setLastReq] = useState<RecommendRequest | null>(null);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [active, setActive] = useState<Recommendation | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function run(req: RecommendRequest) {
    setLastReq(req);
    setPhase("loading");
    const data = await fetchRecommendations(req);
    setRecs(data.recommendations);
    setNotice(
      data.places_source === "no_match"
        ? `Aucun lieu trouvé autour de toi pour « ${req.user_input || "ta demande"} » (rayon 2 km). Voici d'autres idées.`
        : data.places_source === "osm_down"
          ? "Le service de cartes (OpenStreetMap) ne répond pas pour l'instant : impossible de chercher les lieux autour de toi. Voici des idées sans sortir, réessaie dans un moment."
          : null
    );
    setPhase("results");
  }

  return (
    <div className="min-h-screen px-4 py-10 sm:px-8 sm:py-16">
      <header className="mx-auto mb-12 max-w-2xl text-center">
        <motion.h1
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1 }}
          className="text-4xl font-light tracking-tight sm:text-5xl"
        >
          Kairos
        </motion.h1>
        <p className="mt-3 text-muted">Le moment opportun pour décrocher. Trois idées, pas une de plus.</p>
      </header>

      <main className="mx-auto max-w-6xl">
        <AnimatePresence mode="wait">
          {phase === "form" && <KairosForm key="form" initial={lastReq} onSubmit={run} />}
          {phase === "loading" && <BreathingLoader key="loader" />}
          {phase === "results" && (
            <motion.section key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {notice && (
                <p className="mx-auto mb-8 flex max-w-2xl items-center justify-center gap-2 rounded-full bg-card px-5 py-3 text-center text-sm text-muted">
                  <MapPinOff size={15} /> {notice}
                </p>
              )}
              <div className={`grid gap-6 ${recs.length === 2 ? "mx-auto max-w-4xl md:grid-cols-2" : "md:grid-cols-3"}`}>
                {recs.map((r, i) => (
                  <KairosCard key={r.id} rec={r} index={i} onStart={setActive} />
                ))}
              </div>
              <div className="mt-12 flex flex-wrap justify-center gap-3">
                <button
                  onClick={() => setPhase("form")}
                  className="flex items-center gap-2 rounded-full bg-card px-5 py-3 text-sm hover:bg-accent-lilas"
                >
                  <ArrowLeft size={15} /> Modifier ma demande
                </button>
                {lastReq && (
                  <button
                    onClick={() => run(lastReq)}
                    className="flex items-center gap-2 rounded-full bg-card px-5 py-3 text-sm hover:bg-accent-sauge"
                  >
                    <RefreshCw size={15} /> Autres idées
                  </button>
                )}
              </div>
              <p className="mt-10 text-center text-sm text-muted">Choisis-en une, ferme l'onglet, et vas-y.</p>
            </motion.section>
          )}
        </AnimatePresence>
      </main>

      <AnimatePresence>{active && <InstructionModal rec={active} onClose={() => setActive(null)} />}</AnimatePresence>
    </div>
  );
}
