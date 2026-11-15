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
  is_place?: boolean;
  rating?: number | null;
  user_rating_count?: number | null;
  photo_author?: string;
  photo_author_url?: string;
  photo_google_maps_uri?: string;
  opening_hours?: string;
}

export interface RecommendRequest {
  user_input: string;
  mood: string | null;
  is_alone: boolean;
  max_options: number;
  lat?: number | null;
  lon?: number | null;
  radius?: number;
}

export interface RecommendResponse {
  recommendations: Recommendation[];
  source?: "llm" | "fallback" | "mock";
  places_source?: "google" | "maps" | "google_no_match" | "google_not_configured" | "google_error" | "maps_error" | "no_location";
  position?: "gps" | "unavailable";
}
