/* Typy dát, ktoré publikuje agent (src/team_pulse/predict.py) a ich načítanie. */

export type Tier = "Silný" | "Stabilný" | "Oslabený" | "Kritický";

export interface TeamState {
  team: string;
  elo: number;
  elo_today: number;
  pulse: number;
  tier: Tier;
  normal_tier: Tier;
  dropped: boolean;
  reasons: [string, number][];
  confidence?: "vysoká" | "stredná" | "nízka";
  layers?: { strength: number; roster: number; players: number; fatigue: number };
  contributions?: Record<string, number>;
}

export interface Scenario {
  p_home: number;
  pulse: number;
  tier: Tier;
}

export interface WhatIf {
  player_id: number;
  player: string;
  team: string;
  side: "home" | "away";
  p_out: number;
  impact_elo: number;
  plays: Scenario;
  out: Scenario;
}

export interface Game {
  game_id: string;
  date: string;
  tipoff_utc: string;
  neutral: boolean;
  home_adv: number;
  p_home: number;
  margin_home: number;
  home: TeamState;
  away: TeamState;
  what_if: WhatIf[];
}

export interface Meta {
  generated_at: string;
  model: string;
  last_result: string;
  injuries_timestamp?: string;
  injuries_matched?: string;
}

export interface Predictions extends Meta {
  days: Record<string, Game[]>;
}

export interface RosterPlayer {
  player_id: number;
  player: string;
  status: string;
  p_out: number;
  typical_min: number;
  impact_elo: number;
}

export interface TrendPoint {
  date: string;
  opp: string;
  home: boolean;
  pts: number;
  opp_pts: number;
  elo: number;
  pulse: number;
}

export interface TeamPage extends TeamState {
  rank: number;
  trend: TrendPoint[];
  roster: RosterPlayer[];
  upcoming: { game_id: string; date: string; opp: string; home: boolean }[];
}

export interface Teams extends Meta {
  teams: Record<string, TeamPage>;
}

export interface ModelInfo {
  version: string;
  created: string;
  train_seasons: [number, number];
  n_games: number;
  test_metrics: { accuracy: number; log_loss: number; brier: number; test_seasons: string };
  calibration: { band: string; n: number; pred: number; actual: number }[];
  versions: { model: string; accuracy: number; log_loss: number; brier: number }[];
  elo_weights: Record<string, number>;
}

export interface AppData {
  predictions: Predictions;
  teams: Teams;
  model: ModelInfo;
}

async function getJson<T>(name: string): Promise<T> {
  const r = await fetch(`./data/${name}.json`, { cache: "no-store" });
  if (!r.ok) throw new Error(`${name}.json: HTTP ${r.status}`);
  return (await r.json()) as T;
}

export async function loadData(): Promise<AppData> {
  const [predictions, teams, model] = await Promise.all([
    getJson<Predictions>("predictions"),
    getJson<Teams>("teams"),
    getJson<ModelInfo>("model"),
  ]);
  return { predictions, teams, model };
}

export function allGames(p: Predictions): Game[] {
  return Object.values(p.days).flat();
}
