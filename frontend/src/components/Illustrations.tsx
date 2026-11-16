import type { TagColor } from "../types";

// Illustrations plates à contour chaud, dans la palette pastel de l'app.
// Toutes sont aria-hidden : elles n'apportent pas d'information au lecteur d'écran.

const C = {
  outline: "#6B5656",
  cream: "#FFF8EE",
  coral: "#F58C78",
  coralLight: "#FFD2C8",
  sun: "#FFD66B",
  sunLight: "#FFEDB8",
  mint: "#A8E3D2",
  teal: "#3FA990",
  wood: "#E0C397",
  grain: "#C9A774",
};

const s = { stroke: C.outline, strokeWidth: 2.5, strokeLinecap: "round", strokeLinejoin: "round" } as const;

interface SceneProps { className?: string }

// Sortie : soleil, nuage, collines et arbre.
function OutdoorScene({ className }: SceneProps) {
  return (
    <svg viewBox="0 0 200 160" className={className} aria-hidden>
      <circle cx="146" cy="44" r="16" fill={C.sun} {...s} />
      <path d="M146 18v-6M146 76v-6M120 44h-6M178 44h-6M128 26l-4-4M168 66l-4-4M128 62l-4 4M168 22l-4 4" {...s} />
      <path d="M44 50a10 10 0 0 1 19-4a8 8 0 0 1 13 7h-32a6 6 0 0 1 0-3Z" fill={C.cream} {...s} />
      <path d="M8 136C36 96 76 98 104 118S168 104 194 136Z" fill={C.mint} {...s} />
      <path d="M66 120V96" {...s} fill="none" />
      <circle cx="66" cy="82" r="16" fill={C.teal} {...s} />
      <path d="M60 78q6-6 12 0" fill="none" stroke={C.cream} strokeWidth="2.5" strokeLinecap="round" />
      <path d="M8 136H194" {...s} />
      <path d="M100 136q10-8 4-18" fill="none" {...s} strokeDasharray="1 7" />
    </svg>
  );
}

// Création : une feuille dessinée, un crayon, des touches de peinture.
function CreativeScene({ className }: SceneProps) {
  return (
    <svg viewBox="0 0 200 160" className={className} aria-hidden>
      <g transform="rotate(-5 92 84)">
        <rect x="46" y="28" width="92" height="112" rx="5" fill={C.cream} {...s} />
        <rect x="58" y="40" width="68" height="46" rx="3" fill={C.coralLight} {...s} />
        <circle cx="108" cy="54" r="7" fill={C.sun} {...s} />
        <path d="M58 78l18-16l14 12l10-8l26 18" fill="none" {...s} />
        <path d="M58 100h52M58 114h36" fill="none" {...s} />
      </g>
      <g transform="rotate(30 154 84)">
        <rect x="146" y="34" width="16" height="72" rx="2" fill={C.sun} {...s} />
        <rect x="146" y="26" width="16" height="10" rx="2" fill={C.coral} {...s} />
        <path d="M146 106l8 18l8-18Z" fill={C.cream} {...s} />
        <path d="M151.5 118.5l2.5 5.5l2.5-5.5Z" fill={C.outline} />
      </g>
      <circle cx="160" cy="138" r="7" fill={C.coral} {...s} />
      <circle cx="180" cy="128" r="5" fill={C.mint} {...s} />
      <circle cx="28" cy="46" r="4" fill={C.sun} {...s} />
    </svg>
  );
}

// Découverte : un livre ouvert, une loupe et quelques étincelles.
function DiscoveryScene({ className }: SceneProps) {
  return (
    <svg viewBox="0 0 200 160" className={className} aria-hidden>
      <path d="M100 64Q74 50 40 56V128Q74 122 100 136Q126 122 160 128V56Q126 50 100 64Z" fill={C.sun} {...s} />
      <path d="M100 60Q76 46 46 52V122Q76 116 100 130Z" fill={C.cream} {...s} />
      <path d="M100 60Q124 46 154 52V122Q124 116 100 130Z" fill={C.cream} {...s} />
      <path d="M58 70q16-5 30 1M58 84q16-5 30 1M58 98q16-5 30 1M112 71q14-6 30-1M112 85q14-6 30-1" fill="none" {...s} strokeWidth="2" />
      <circle cx="140" cy="104" r="14" fill={C.mint} fillOpacity=".7" {...s} />
      <path d="M150 114l14 14" {...s} strokeWidth="5" />
      <path d="M96 16l3 8l8 3l-8 3l-3 8l-3-8l-8-3l8-3Z" fill={C.coral} {...s} strokeWidth="2" />
      <path d="M58 30v10M53 35h10M142 26v10M137 31h10" {...s} />
    </svg>
  );
}

const SCENES: Record<TagColor, (p: SceneProps) => JSX.Element> = {
  sauge: OutdoorScene,
  peche: CreativeScene,
  lilas: DiscoveryScene,
};

export function CategoryIllustration({ color, className }: { color: TagColor; className?: string }) {
  const Scene = SCENES[color] ?? OutdoorScene;
  return <Scene className={className} />;
}

// Accueil : une étagère en bois où le téléphone dort, face contre la planche,
// entouré de ce qui le remplace : un thé, des livres, une plante, des crayons.
export function HeroIllustration({ className }: { className?: string }) {
  return (
    <svg viewBox="0 44 480 156" className={className} aria-hidden>
      {/* ombre et planche */}
      <rect x="30" y="182" width="420" height="10" rx="5" fill="#000" opacity=".06" />
      <rect x="20" y="164" width="440" height="18" rx="3" fill={C.wood} {...s} />
      <path d="M60 172h60M150 175h90M290 171h70M390 175h40" stroke={C.grain} strokeWidth="2" strokeLinecap="round" />
      <circle cx="34" cy="173" r="2.5" fill={C.outline} />
      <circle cx="446" cy="173" r="2.5" fill={C.outline} />

      {/* tasse de thé */}
      <path d="M56 104h56v46a14 14 0 0 1-14 14h-28a14 14 0 0 1-14-14Z" fill={C.cream} {...s} />
      <path d="M56 104h56v14H56Z" fill={C.coral} {...s} />
      <path d="M112 122h6a14 14 0 0 1 0 28h-6" fill="none" stroke={C.coral} strokeWidth="9" />
      <path d="M112 117h6a19 19 0 0 1 0 38h-6M112 127h6a9 9 0 0 1 0 18h-6" fill="none" {...s} />
      <path d="M74 92q-6-9 0-18t0-18M92 92q-6-9 0-18" fill="none" {...s} opacity=".6" />

      {/* pile de livres */}
      <rect x="146" y="148" width="86" height="16" rx="2" fill={C.mint} {...s} />
      <rect x="152" y="132" width="74" height="16" rx="2" fill={C.sun} {...s} />
      <rect x="148" y="118" width="80" height="14" rx="2" fill={C.coral} {...s} />
      <path d="M160 156h40M164 140h30M160 125h36" stroke={C.outline} strokeWidth="2" strokeLinecap="round" opacity=".5" />

      {/* téléphone retourné, qui dort */}
      <rect x="248" y="152" width="80" height="12" rx="5" fill="#CFC3E6" {...s} />
      <path d="M296 128h10l-10 11h10M314 108h7l-7 8h7" fill="none" {...s} />

      {/* plante */}
      <path d="M346 130h40l-5 34h-30Z" fill={C.coral} {...s} />
      <path d="M342 124h48v10h-48Z" fill={C.coralLight} {...s} />
      <path d="M366 124V72" fill="none" {...s} />
      <path d="M366 112c-20 0-28-14-26-28c16 0 26 10 26 28Z" fill={C.teal} {...s} />
      <path d="M366 98c18 0 26-14 24-30c-16 2-24 12-24 30Z" fill={C.mint} {...s} />
      <path d="M366 80c-10-6-12-18-6-28c8 6 10 16 6 28Z" fill={C.teal} {...s} />

      {/* pot à crayons */}
      <rect x="408" y="78" width="10" height="56" rx="2" fill={C.sun} {...s} />
      <path d="M408 78l5-12l5 12Z" fill={C.cream} {...s} />
      <rect x="422" y="90" width="10" height="44" rx="2" fill={C.coral} {...s} />
      <path d="M422 90l5-12l5 12Z" fill={C.cream} {...s} />
      <path d="M402 118h36v40a6 6 0 0 1-6 6h-24a6 6 0 0 1-6-6Z" fill={C.cream} fillOpacity=".9" {...s} />
      <path d="M402 118h36v8h-36Z" fill={C.mint} {...s} />
    </svg>
  );
}
