import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, RefreshCw, MapPinOff, History } from "lucide-react";
import KairosForm from "./components/KairosForm";
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
            ? "Aucun lieu ouvert près de toi ne correspond au type demandé avec une note suffisante et une photo. Essaie une de ces trois idées."
            : data.places_source === "google_error"
              ? "Google Places n'a pas répondu. Voici trois idées à faire; vérifie la clé et l'activation de Places API."
              : data.places_source === "maps_error"
                ? "Google Maps n'a pas répondu. Voici trois idées à faire; réessaie dans un instant."
                : null
    );
    setPhase("results");
  }

  return (
    <div className="min-h-screen px-4 py-12 sm:px-8 sm:py-20">
      <header className="mx-auto mb-14 max-w-2xl text-center">
        <motion.h1
          initial={{ opacity: 0, letterSpacing: "0.08em" }}
          animate={{ opacity: 1, letterSpacing: "-0.02em" }}
          transition={{ duration: 1.6, ease: "easeOut" }}
          className="font-serif text-6xl font-normal text-ink sm:text-7xl"
        >
          Kairos
        </motion.h1>
        <p className="mt-3 font-serif text-lg italic text-muted">καιρός, le moment opportun</p>
        <button
          onClick={async () => { setHistory(await fetchHistory()); setShowHistory(!showHistory); }}
          aria-expanded={showHistory}
          className="mt-6 inline-flex items-center gap-2 text-sm text-muted underline-offset-4 transition-colors hover:text-ink hover:underline"
        >
          <History size={15} /> {showHistory ? "Masquer mes activités faites" : "Mes activités faites"}
        </button>
      </header>

      <main className="mx-auto max-w-6xl">
        {showHistory && (
          <section className="mx-auto mb-10 max-w-2xl rounded-2xl bg-surface p-6">
            <h2 className="font-serif text-xl text-ink">Activités faites</h2>
            {history.length ? (
              <ul className="mt-4 divide-y divide-line">
                {history.map((item) => (
                  <li key={item.id} className="flex items-baseline justify-between gap-4 py-2.5 text-sm">
                    <span className="text-ink">{item.title}</span>
                    <time className="shrink-0 text-muted">{new Date(item.completed_at).toLocaleDateString("fr-FR")}</time>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-muted">Rien pour l'instant. Marque une idée comme faite et elle apparaîtra ici.</p>
            )}
          </section>
        )}
        <AnimatePresence mode="wait">
          {phase === "form" && <KairosForm key="form" initial={lastReq} onSubmit={run} />}
          {phase === "loading" && <BreathingLoader key="loader" />}
          {phase === "results" && (
            <motion.section key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {notice && (
                <p role="status" className="mx-auto mb-10 flex max-w-2xl items-start gap-3 rounded-xl border border-line px-5 py-4 text-sm leading-relaxed text-muted">
                  <MapPinOff size={16} className="mt-0.5 shrink-0" /> {notice}
                </p>
              )}
              <div className={`grid items-start gap-5 ${recs.length === 2 ? "mx-auto max-w-4xl md:grid-cols-2" : "md:grid-cols-3"}`}>
                {recs.map((r, i) => (
                  <KairosCard key={r.id} rec={r} index={i} onStart={setActive} onDone={markDone} />
                ))}
              </div>
              <p className="mt-14 text-center font-serif text-xl italic text-ink">Choisis-en une, pose ton téléphone, et vas-y.</p>
              <div className="mt-6 flex flex-wrap justify-center gap-3">
                <button
                  onClick={() => setPhase("form")}
                  className="flex items-center gap-2 rounded-full border border-line px-5 py-2.5 text-sm text-ink transition-colors hover:border-ink/40"
                >
                  <ArrowLeft size={15} /> Modifier ma demande
                </button>
                {lastReq && (
                  <button
                    onClick={() => run(lastReq)}
                    className="flex items-center gap-2 rounded-full border border-line px-5 py-2.5 text-sm text-ink transition-colors hover:border-ink/40"
                  >
                    <RefreshCw size={15} /> Trois autres idées
                  </button>
                )}
              </div>
            </motion.section>
          )}
        </AnimatePresence>
      </main>

      <AnimatePresence>{active && <InstructionModal rec={active} onClose={() => setActive(null)} />}</AnimatePresence>
    </div>
  );
}
