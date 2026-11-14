export type TagColor = "sauge" | "peche" | "lilas";

export interface Recommendation {
  id: string;
  type: "indoor" | "outdoor";
  category_tag: string;
  tag_color: TagColor;
  title: string;
  location_name: string;
  image_url: string;
  description: string;
  maps_url: string | null;
  instructions?: string[];
  lat?: number | null;
  lon?: number | null;
  distance_m?: number | null;
}

export interface RecommendRequest {
  user_input: string;
  mood: string | null;
  is_alone: boolean;
  max_options: number;
  lat?: number;
  lon?: number;
  radius?: number;
}

export interface RecommendResponse {
  recommendations: Recommendation[];
  source?: "llm" | "fallback" | "mock";
  places_source?: "osm" | "osm_match" | "no_match" | "catalogue" | "none";
  position?: "gps" | "rabat";
}
