/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Base : calcaire chaud et encre vert pin, peu stimulant pour l'œil.
        paper: "#E6DECE",
        surface: "#F1EBDD",
        ink: "#283028",
        muted: "#575C4F",
        line: "#D5CAB4",
        // Une teinte par catégorie d'activité.
        moss: "#5F7D5A", // sortie
        amber: "#A86A28", // création
        iris: "#6E6388", // découverte
        // Alias conservés pour les anciennes classes.
        canvas: "#E6DECE",
        card: "#F1EBDD",
        charcoal: "#283028",
        accent: { sauge: "#DCE5D6", peche: "#EFE0C9", lilas: "#E3DCEC" },
      },
      fontFamily: {
        serif: ['"Fraunces"', "Georgia", "serif"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
      borderRadius: { "4xl": "2rem" },
    },
  },
  plugins: [],
};
