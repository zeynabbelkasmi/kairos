import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, RefreshCw, MapPinOff, History } from "lucide-react";
import KairosForm, { formatRadius } from "./components/KairosForm";
import BreathingLoader from "./components/BreathingLoader";
import KairosCard from "./components/KairosCard";
import InstructionModal from "./components/InstructionModal";
import { fetchHistory, fetchRecommendations, markActivityDone } from "./api";
import type { Recommendation, RecommendRequest } from "./types";

type Phase = "form" | "loading" | "results";

export default function App() {
  const [phase, setPhase] = useState<Phase>("form");
  const [lastReq, setLastReq] = useState<RecommendRequest | null>(null);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [active, setActive] = useState<Recommendation | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [history, setHistory] = useState<{ id: number; title: string; category_tag: string; completed_at: string }[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  async function markDone(rec: Recommendation) {
    try {
      await markActivityDone(rec);
      setNotice(`« ${rec.title} » ajoutée à ton historique.`);
      setHistory(await fetchHistory());
    } catch {
      setNotice("Impossible d'enregistrer cette activité. Vérifie que le serveur est démarré.");
    }
  }

  async function run(req: RecommendRequest) {
    setLastReq(req);
    setPhase("loading");
    let data: Awaited<ReturnType<typeof fetchRecommendations>>;
    try {
      data = await fetchRecommendations(req);
    } catch {
      setRecs([]);
      setNotice("Le serveur de recommandations est indisponible. Démarre le backend puis réessaie.");
      setPhase("results");
      return;
    }
    setRecs(data.recommendations);
    setNotice(
      data.places_source === "google_not_configured"
        ? "Les trois idées sont prêtes, mais aucun spot n'est affiché comme vérifié. Ajoute une clé Google Places API pour obtenir des lieux notés et leurs photos."
        : data.places_source === "no_location"
          ? "La géolocalisation est indisponible. Voici trois activités sans lieu inventé; autorise ta position pour chercher des spots proches."
          : data.places_source === "google_no_match"
            ? `Aucun spot à moins de ${formatRadius(req.radius ?? 2000)} ne correspond au type demandé avec une note suffisante et une photo. Élargis la distance ou essaie une de ces trois idées.`
            : data.places_source === "google_error"
              ? "Google Places n'a pas répondu. Voici trois idées à faire; vérifie la clé et l'activation de Places API."
              : data.places_source === "maps_error"
                ? "Google Maps n'a pas répondu. Voici trois idées à faire; réessaie dans un instant."
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
        <button onClick={async () => { setHistory(await fetchHistory()); setShowHistory(!showHistory); }} className="mt-4 inline-flex items-center gap-2 rounded-full bg-card px-4 py-2 text-sm text-muted hover:bg-accent-lilas">
          <History size={15} /> {showHistory ? "Masquer l'historique" : "Mes activités faites"}
        </button>
      </header>

      <main className="mx-auto max-w-6xl">
        {showHistory && <section className="mx-auto mb-8 max-w-2xl rounded-3xl bg-card p-6"><h2 className="mb-3 font-semibold">Activités terminées</h2>{history.length ? <ul className="space-y-2">{history.map((item) => <li key={item.id} className="text-sm text-muted">{item.title} <span className="opacity-70">· {new Date(item.completed_at).toLocaleDateString("fr-FR")}</span></li>)}</ul> : <p className="text-sm text-muted">Aucune activité enregistrée pour le moment.</p>}</section>}
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
                  <KairosCard key={r.id} rec={r} index={i} onStart={setActive} onDone={markDone} />
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
