import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api/v1";

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

export type ScoutPlayerOption = {
  player_name: string;
  club: string | null;
};

export type ScoutPlayerHeader = {
  player_name: string;
  season: string;
  position: string | null;
  nationality: string | null;
  club: string | null;
  player_picture: string | null;
  club_crest: string | null;
  nation_flag: string | null;
  preferred_foot: string | null;
  age: number | null;
  height: number | null;
  market_value: string | null;
  goals_this_season: number | null;
  assists_this_season: number | null;
  xg_this_season: number | null;
  xa_this_season: number | null;
  yellow_cards: number | null;
  red_cards: number | null;
  matches_played: number;
  confidence: "high" | "medium" | "low";
  confidence_reason: string | null;
  last_updated: string | null;
};

export type SpatialProfile = {
  player_name: string;
  league: string;
  season: string;
  pos_group: string;
  percentiles_2526: Record<string, number>;
  style_cluster: { cluster_label: string; };
  touch_heatmap?: {
    all: number[][];
    passes: number[][];
    carries: number[][];
    defensive: number[][];
  };
};

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("auth_token");
      window.dispatchEvent(new Event("auth:unauthorized"));
    }
    return Promise.reject(error);
  },
);

export async function fetchScoutPlayerOptions(
  season = "25-26",
  limit = 200,
  search?: string,
): Promise<ScoutPlayerOption[]> {
  const response = await client.get<ScoutPlayerOption[]>("/scout-reports/players/options", {
    params: { season, limit, search },
  });
  return response.data;
}

export async function fetchScoutPlayerHeader(
  playerName: string,
  season = "25-26",
  club?: string,
): Promise<ScoutPlayerHeader> {
  const response = await client.get<ScoutPlayerHeader>("/scout-reports/player-header", {
    params: {
      player_name: playerName,
      season,
      club,
    },
  });
  return response.data;
}

export async function fetchDevAccessToken(): Promise<string> {
  const response = await client.post<{ access_token: string; token_type: string }>("/auth/dev-login");
  return response.data.access_token;
}

export async function fetchSpatialProfile(
  playerName: string,
  season = "2025/2026",
): Promise<SpatialProfile> {
  const response = await client.get<SpatialProfile>("/spatial/profile", {
    params: {
      player_name: playerName,
      season,
    },
  });
  return response.data;
}

export default client;
