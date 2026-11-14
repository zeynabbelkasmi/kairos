/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#FDFBF7",
        card: "#F4F1EA",
        charcoal: "#4A4641",
        muted: "#7A756E",
        accent: { lilas: "#E0D8EA", sauge: "#D2E0D9", peche: "#F6E3D4" },
      },
      fontFamily: { sans: ['"Plus Jakarta Sans"', "Inter", "system-ui", "sans-serif"] },
      borderRadius: { "4xl": "2rem" },
    },
  },
  plugins: [],
};
