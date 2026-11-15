import type { RecommendRequest, RecommendResponse } from "./types";

/** Position GPS réelle ; pas de substitution silencieuse par une autre ville. */
function getPosition(): Promise<{ lat: number | null; lon: number | null; source: "gps" | "unavailable" }> {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve({ lat: null, lon: null, source: "unavailable" });
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lon: p.coords.longitude, source: "gps" }),
      () => resolve({ lat: null, lon: null, source: "unavailable" }),
      { timeout: 8000, maximumAge: 300000 }
    );
  });
}

/** Appelle le backend avec la position ; si indisponible, renvoie les donnÃ©es factices. */
export async function fetchRecommendations(req: RecommendRequest): Promise<RecommendResponse> {
  const minDelay = new Promise((r) => setTimeout(r, 1800)); // laisse respirer l'animation
  const pos = await getPosition();
  try {
    const res = await fetch("/api/kairos/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...req, lat: pos.lat, lon: pos.lon, radius: req.radius ?? 2000 }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = (await res.json()) as RecommendResponse;
    await minDelay;
    return { ...data, position: pos.source };
  } catch (e) {
    await minDelay;
    throw e;
  }
}

export async function markActivityDone(activity: { id: string; title: string; category_tag: string }) {
  const res = await fetch("/api/kairos/history", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ activity_id: activity.id, title: activity.title, category_tag: activity.category_tag }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchHistory(): Promise<{ id: number; activity_id: string; title: string; category_tag: string; completed_at: string }[]> {
  const res = await fetch("/api/kairos/history");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
