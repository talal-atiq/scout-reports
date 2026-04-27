import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api/v1";

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
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
  per_90: Record<string, number>;
  percentiles_2526: Record<string, number>;
  style_cluster: { cluster_label: string; };
  confidence_score?: number;
  sub_role?: string;
  touch_heatmap?: {
    all: number[][];
    passes: number[][];
    carries: number[][];
    defensive: number[][];
  };
  shot_zones?: {
    x: number;
    y: number;
    goal_mouth_y: number;
    goal_mouth_z: number;
    result: "Goal" | "SavedShot" | "MissedShot" | "BlockedShot";
    is_big_chance: boolean;
    is_left_foot: boolean;
    is_right_foot: boolean;
    is_header: boolean;
    xT: number | null;
    minute: number;
  }[];
  xT_zones?: {
    grid: number[][];
    xT_per_touch_grid: number[][];
  };
  pass_vectors?: {
    from_row: number;
    from_col: number;
    to_row: number;
    to_col: number;
    start_zone: string;
    start_depth: string;
    end_zone: string;
    end_depth: string;
    frequency: number;
    success_rate: number;
    avg_xT_gain: number;
    avg_prog_dist: number;
  }[];
  pass_cluster_distribution?: Record<string, number>;
};

export interface LeagueProjectionPoint {
  player_name: string;
  raw_value: number;
  z_score: number;
  translated_z_score: number;
  is_target: boolean;
}

export interface LeagueProjectionResult {
  league: string;
  league_weight: number;
  league_points: number;
  mean: number;
  std: number;
  projected_impact?: number;
  players: LeagueProjectionPoint[];
}

export interface LeagueProjectionResponse {
  metric: string;
  target_player: string;
  target_raw_value: number;
  pos_group: string;
  peer_filter_active: boolean;
  cluster_label: string | null;
  impact_composition?: string;
  leagues: LeagueProjectionResult[];
}

export interface TacticalTwin {
  player_id: string;
  name: string;
  club: string;
  league: string;
  minutes: number;
  similarity: number;
  confidence: string;
  role: string;
  insight: string;
  style_cluster: string;
  pca_x: number;
  pca_y: number;
}

export interface TacticalTwinResponse {
  target: {
    name: string;
    role: string;
    insight: string;
    pca_x: number;
    pca_y: number;
  };
  twins: TacticalTwin[];
}

export interface ScatterPlayer {
  player_id: string;
  player_name: string;
  league: string;
  pos_group: string;
  style_cluster: string;
  matches_processed: number;
  minutes_played: number;
  stats: Record<string, number>;
}

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

export interface TransferMarketData {
  player: string;
  market_value: number;
  mv_history: Record<string, number>;
  [key: string]: any;
}

export async function fetchLeagueProjection(
  playerName: string,
  season: string,
  metric: string,
  peerFilter: boolean
): Promise<LeagueProjectionResponse> {
  const response = await client.get<LeagueProjectionResponse>("/spatial/league-projection", {
    params: {
      player_name: playerName,
      season,
      metric,
      peer_filter: peerFilter,
    },
  });
  return response.data;
}

export async function fetchTransferMarketData(playerName: string): Promise<TransferMarketData> {
  const response = await client.get<TransferMarketData>("/transfer-market/player", {
    params: { player_name: playerName },
  });
  return response.data;
}

export async function fetchTacticalTwins(
  playerName: string,
  season = "2025/2026"
): Promise<TacticalTwinResponse> {
  const response = await client.get<TacticalTwinResponse>("/spatial/tactical-twins", {
    params: { player_name: playerName, season },
  });
  return response.data;
}

export async function fetchScatterData(
  season = "2025/2026",
  minMatches = 10
): Promise<ScatterPlayer[]> {
  const response = await client.get<ScatterPlayer[]>("/spatial/scatter", {
    params: { season, min_matches: minMatches },
  });
  return response.data;
}

export interface AiScoutReportResponse {
  executive_summary: string;
  pizza_chart_analysis: string;
  heatmap_analysis: string;
  skill_translation_analysis: string;
  expected_threat_analysis: string;
  passing_corridors_analysis: string;
  positive_development_factors: string[];
  concerns_and_next_steps: string[];
}

export const fetchAiScoutReport = async (playerName: string, season: string = "25-26"): Promise<AiScoutReportResponse> => {
  const res = await client.post('/ai/scout-report', { player_name: playerName, season });
  return res.data;
};

export default client;
