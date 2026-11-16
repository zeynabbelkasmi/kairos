/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Base : blanc chaud, rose poudré, encre brun doux.
        paper: "#FFFCFA",
        blush: "#FFF1EC",
        surface: "#FFFFFF",
        ink: "#4A3B3B",
        muted: "#7A6767",
        line: "#F1DDD6",
        // Accents pastel inspirés des illustrations.
        coral: { DEFAULT: "#F0715C", deep: "#C64A36", light: "#FFE3DC" },
        sun: { DEFAULT: "#FFD66B", light: "#FFF0C7" },
        mint: { DEFAULT: "#A8E3D2", deep: "#1F8574", light: "#D9F3EA" },
        wood: "#E0C397",
        // Alias conservés pour les anciennes classes.
        canvas: "#FFFCFA",
        card: "#FFF1EC",
        charcoal: "#4A3B3B",
      },
      fontFamily: {
        serif: ['"Nunito"', "system-ui", "sans-serif"],
        sans: ['"Nunito"', "system-ui", "sans-serif"],
        script: ['"Dancing Script"', "cursive"],
      },
      boxShadow: {
        soft: "0 1px 0 #F1DDD6, 0 10px 30px -18px rgba(198, 74, 54, 0.35)",
      },
      borderRadius: { "4xl": "2rem" },
    },
  },
  plugins: [],
};
