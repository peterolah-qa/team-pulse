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
  kind?: string; // "preseason" = prípravný zápas
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

export interface BoxRow {
  player: string;
  min: number;
  pts: number;
  reb: number;
  ast: number;
  blk: number;
  stl: number;
}

/* Dohraný zápas z posledných dní: skóre, náš tip pred zápasom (z archívu) a štatistiky hráčov. */
export interface Result {
  game_id: string;
  date: string;
  kind?: string;
  home: string;
  away: string;
  pts_home: number;
  pts_away: number;
  tipoff_utc?: string;
  p_home: number | null;
  box: Record<string, BoxRow[]>;
}

export interface Predictions extends Meta {
  days: Record<string, Game[]>;
  results?: Result[];
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
  upcoming: { game_id: string; date: string; opp: string; home: boolean; kind?: string; tipoff_utc?: string }[];
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

// --- NHL (beta): zamknuté tipy z archívu a výsledky, publikuje src/team_pulse/nhl/app_data.py ---

export type Sport = "nba" | "nhl";

export interface NhlSide {
  team: string;
  elo: number;
  reasons: [string, number][]; // únava a cestovanie v Elo bodoch, od najväčšieho vplyvu
}

/* Kontext zápasu pre detail (src/team_pulse/nhl/context.py). Len informácia, tip sa podľa neho nemení. */
export type NhlOutcome = "W" | "L" | "OTL"; // OTL = prehra po predĺžení alebo nájazdoch

export interface NhlEdge {
  verified: boolean; // model z rozpisu klubov znova vypočítal presne zamknutú šancu
  total: number; // Elo body z pohľadu domácich, dajú zamknutú šancu
  items: [string, string, number][]; // [kľúč, popis, Elo body z pohľadu domácich], súčet = total
}

export interface NhlLastGame {
  date: string;
  opp: string;
  home: boolean;
  gf: number;
  ga: number;
  res: NhlOutcome;
  last: "OT" | "SO" | null;
}

export interface NhlForm {
  gp: number;
  record: [number, number, number]; // výhry, prehry, prehry po predĺžení alebo nájazdoch (základná časť)
  home_record: [number, number, number];
  road_record: [number, number, number];
  gf_pg: number | null;
  ga_pg: number | null;
  last: NhlLastGame[]; // od najnovšieho
}

export interface NhlRest {
  prev: { date: string; opp: string; home: boolean; res: NhlOutcome } | null;
  rest?: number; // dni od posledného zápasu (1 = back-to-back, najviac 7) – rovnako ako vstup modelu
  b2b?: boolean;
  three_in4?: boolean;
  tz_east?: number;
  road?: number;
}

export type NhlStatKey = "gf" | "ga" | "pp" | "pk" | "sf" | "sa";
export type NhlStats = Record<NhlStatKey, number> & { gp: number; w: number; rank: Record<NhlStatKey, number> };

export interface NhlTeamCtx {
  form: NhlForm;
  rest: NhlRest;
  stats?: NhlStats;
}

export interface NhlH2H {
  date: string;
  home: string;
  away: string;
  gh: number;
  ga: number;
  last: "OT" | "SO" | null;
  type: "R" | "P";
}

export interface NhlCtx {
  edge: NhlEdge;
  trend: { home: [string, number][]; away: [string, number][] };
  venue?: string | null;
  home?: NhlTeamCtx;
  away?: NhlTeamCtx;
  h2h?: NhlH2H[];
}

export interface NhlGame {
  game_id: string;
  date: string;
  tipoff_utc: string;
  kind?: string;
  neutral: boolean;
  p_home: number;
  locked_at: string;
  home: NhlSide;
  away: NhlSide;
  ctx?: NhlCtx;
}

export interface NhlResult {
  game_id: string;
  date: string;
  tipoff_utc: string;
  kind?: string;
  home: string;
  away: string;
  goals_home: number;
  goals_away: number;
  last_period: string | null; // REG, OT (po predĺžení), SO (po nájazdoch)
  p_home: number | null;
}

export interface NhlInjury {
  player: string;
  pos: string | null;
  status: "OUT" | "SUSP" | "IR" | "DTD" | "?";
  injury: string | null; // ESPN po anglicky („Upper Body“)
  return_date: string | null; // odhad ESPN, YYYY-MM-DD
  updated: string | null;
}

export interface NhlPredictions {
  generated_at: string;
  beta: boolean;
  model: string;
  last_locked: string | null;
  days: Record<string, NhlGame[]>;
  results: NhlResult[];
  teams: { team: string; elo: number; as_of: string }[];
  injuries?: Record<string, NhlInjury[]> | null; // ESPN, len informácia – model NHL ich nepoužíva
  injuries_timestamp?: string | null;
  context_at?: string | null;
  stats_at?: string | null;
}

export interface NhlData {
  predictions: NhlPredictions;
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

export async function loadNhl(): Promise<NhlData> {
  const [predictions, model] = await Promise.all([getJson<NhlPredictions>("nhl/predictions"), getJson<ModelInfo>("nhl/model")]);
  return { predictions, model };
}

export function allGames(p: Predictions): Game[] {
  return Object.values(p.days).flat();
}
