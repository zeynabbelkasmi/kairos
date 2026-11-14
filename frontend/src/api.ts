import type { RecommendRequest, RecommendResponse } from "./types";
import { MOCK_RESPONSE } from "./mockData";

const RABAT = { lat: 34.0209, lon: -6.8416 };

/** Position GPS de l'utilisateur ; Rabat centre si refusée ou indisponible. */
function getPosition(): Promise<{ lat: number; lon: number; source: "gps" | "rabat" }> {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve({ ...RABAT, source: "rabat" });
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lon: p.coords.longitude, source: "gps" }),
      () => resolve({ ...RABAT, source: "rabat" }),
      { timeout: 8000, maximumAge: 300000 }
    );
  });
}

/** Appelle le backend avec la position ; si indisponible, renvoie les données factices. */
export async function fetchRecommendations(req: RecommendRequest): Promise<RecommendResponse> {
  const minDelay = new Promise((r) => setTimeout(r, 1800)); // laisse respirer l'animation
  const pos = await getPosition();
  try {
    const res = await fetch("/api/kairos/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...req, lat: pos.lat, lon: pos.lon, radius: 2000 }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = (await res.json()) as RecommendResponse;
    await minDelay;
    return { ...data, position: pos.source };
  } catch (e) {
    console.warn("Backend indisponible, données factices utilisées.", e);
    await minDelay;
    return { ...MOCK_RESPONSE, recommendations: MOCK_RESPONSE.recommendations.slice(0, req.max_options) };
  }
}
