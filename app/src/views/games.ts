/* Zápasy: najbližšie zápasy po dňoch v našom čase. Jeden zápas = hostia a domáci pod sebou, vpravo šanca. */
import type { AppData, Game, ModelInfo, Sport, TeamState, Tier } from "../data";
import { allGames } from "../data";
import { badge, chip, esc, oddsBar, parseUtc, pulseNum, split, TEAM_NAMES, TIERS, tierClass, time, when } from "../ui";
import { card, dayWidget, fav, matchesPage, topReasons, type CardSide } from "./matches";

/* Čo riadok zápasu potrebuje – spĺňa NBA aj NHL zápas. NBA má navyše Pulse a úroveň. */
interface Side {
  team: string;
  reasons: [string, number][];
  pulse?: number;
  tier?: Tier;
}
export interface RowGame {
  game_id: string;
  date: string;
  tipoff_utc?: string;
  kind?: string;
  neutral: boolean;
  p_home: number;
  home: Side;
  away: Side;
}

export const isPre = (g: { kind?: string }): boolean => g.kind === "preseason";

/* Chýbajúci hráči z dôvodov modelu („Bez X (?)“), najviac jeden na team. */
function absences(g: RowGame): string[] {
  return [g.away, g.home].flatMap((s) => {
    const r = s.reasons.find(([t]) => t.startsWith("Bez "));
    return r ? [`${s.team}: ${r[0].charAt(0).toLowerCase()}${r[0].slice(1)}`] : [];
  });
}

/* Prstenec formy pri NBA (Pulse vo farbe úrovne); NHL Pulse nemá, odznak je bez prstenca. */
export const pulseRing = (s: Side) => (s.pulse !== undefined && s.tier ? { value: s.pulse, tone: tierClass(s.tier) } : undefined);

function line(s: Side, p: number, isFav: boolean, home: boolean, sport: Sport): string {
  return `<div class="tl${isFav ? " fav" : ""}">
      ${badge(s.team, sport, "sm", pulseRing(s))}<span class="abbr">${esc(s.team)}</span>${home ? `<span class="home">doma</span>` : ""}
      ${isFav ? `<span class="tip">tip</span>` : ""}
      <span class="val">${p} %</span></div>`;
}

/* Stav zápasu podľa času: ešte nezačal, hrá sa (do 3 h od začiatku), alebo už čaká na výsledok. */
export function liveTag(g: { tipoff_utc?: string }, now: number): string {
  const tip = parseUtc(g.tipoff_utc)?.getTime();
  if (!tip || now < tip) return "";
  return now - tip < 3 * 3600_000 ? `<span class="tag live">hrá sa</span>` : `<span class="tag">po zápase</span>`;
}

/* Jeden zápas v zozname. NBA: poznámka = chýbajúci hráči; NHL si poznámky (únava) pošle sama. */
export function gameRow(g: RowGame, now: number = Date.now(), opt: { sport?: Sport; notes?: string[] } = {}): string {
  const { home, away } = split(g.p_home);
  const homeFav = g.p_home > 0.5; // rovnako ako pri vyhodnotení: presne 50 % = tip na hostí
  const sport = opt.sport ?? "nba";
  const notes = opt.notes ?? absences(g);
  const favSide = homeFav ? g.home : g.away;
  const tone = favSide.tier ? ` tone-${tierClass(favSide.tier)}` : "";
  return `<li><a class="match${tone}" href="#/${sport === "nhl" ? "nhl/" : ""}zapas/${esc(g.game_id)}">
    <div class="when"><span class="clock">${time(g.tipoff_utc)}</span>${liveTag(g, now)}${isPre(g) ? `<span class="tag">príprava</span>` : ""}</div>
    <div class="teams">${line(g.away, away, !homeFav, false, sport)}${line(g.home, home, homeFav, !g.neutral, sport)}${oddsBar(g.p_home)}</div>
    ${notes.length || g.neutral ? `<p class="note">${[g.neutral ? "neutrálne ihrisko" : "", ...notes].filter(Boolean).map(esc).join(" · ")}</p>` : ""}
  </a></li>`;
}

export function byTipoff<T extends { tipoff_utc?: string; game_id: string }>(a: T, b: T): number {
  const ta = parseUtc(a.tipoff_utc)?.getTime() ?? 0, tb = parseUtc(b.tipoff_utc)?.getTime() ?? 0;
  return ta - tb || a.game_id.localeCompare(b.game_id);
}

/* NBA karta: prstence = Pulse teamu, dôvody = vplyvy modelu v prospech tipu. */
function nbaSide(s: TeamState): CardSide {
  return {
    ring: { value: s.pulse, tone: tierClass(s.tier) },
    name: TEAM_NAMES[s.team] ?? s.team,
    line: `Pulse <b class="num">${pulseNum(s.pulse)}</b> ${chip(s.tier)}${s.dropped ? ` <span class="muted">normálne ${esc(s.normal_tier)}</span>` : ""}`,
  };
}

export function nbaCard(g: Game, i: number, n: number, now: number): string {
  const f = fav(g);
  const reasons = [g.away, g.home].flatMap((s) => s.reasons.map(([t, e]): [string, number] => [`${s.team}: ${t}`, s.team === f.team ? e : -e]));
  const favState = f.home ? g.home : g.away;
  return card(g, "nba", { href: `#/zapas/${esc(g.game_id)}`, away: nbaSide(g.away), home: nbaSide(g.home), reasons: topReasons(reasons), tone: tierClass(favState.tier) }, i, n, now);
}

const GROUP: Record<Tier, string> = { Silný: "Silní", Stabilný: "Stabilní", Oslabený: "Oslabení", Kritický: "Kritickí" };

/* Liga podľa formy: počet teamov v každej úrovni ako jeden pruh. */
export function leagueWidget(d: AppData): string {
  const all = Object.values(d.teams.teams);
  if (!all.length) return "";
  const counts = TIERS.map((t) => [t, all.filter((x) => x.tier === t).length] as const);
  const bar = counts.map(([t, c]) => (c ? `<i class="${tierClass(t)}" style="flex:${c}"></i>` : "")).join("");
  const legend = counts.map(([t, c]) => `<li class="${tierClass(t)}"><span class="dot" aria-hidden="true"></span>${GROUP[t]} <b class="num">${c}</b></li>`).join("");
  return `<section class="card widget"><h2 class="label">Liga podľa formy</h2>
    <div class="tierbar" aria-hidden="true">${bar}</div><ul class="tierlegend">${legend}</ul>
    <a class="wlink" href="#/teamy">Všetky teamy podľa Pulse ›</a></section>`;
}

export function modelWidget(m: ModelInfo, href: string): string {
  return `<section class="card widget"><h2 class="label">Model ${esc(m.version)}</h2>
    <div class="kpis two"><div class="kpi"><span class="kpi-n num">${(m.test_metrics.accuracy * 100).toFixed(1).replace(".", ",")} %</span><span class="kpi-l">trafený víťaz v teste</span></div>
      <div class="kpi"><span class="kpi-n num">${m.test_metrics.log_loss.toFixed(4).replace(".", ",")}</span><span class="kpi-l">log loss (menej = lepšie)</span></div></div>
    <a class="wlink" href="${href}">Presnosť a kalibrácia ›</a></section>`;
}

export function gamesView(d: AppData): string {
  const p = d.predictions;
  const finished = new Set((p.results ?? []).map((r) => r.game_id)); // dohrané sú už vo Výsledkoch
  const games = allGames(p).filter((g) => !finished.has(g.game_id)).sort(byTipoff);
  const byId = new Map(games.map((g) => [g.game_id, g]));
  return matchesPage({
    sport: "nba",
    games,
    sub: `aktualizované ${esc(when(p.generated_at))}`,
    card: (g, i, n, now) => nbaCard(byId.get(g.game_id)!, i, n, now),
    row: (g, now) => gameRow(g, now),
    widgets: (day, gs) => `${dayWidget(day, gs, "nba")}${leagueWidget(d)}${modelWidget(d.model, "#/model")}`,
    footer: "Časy sú v našom čase. Tip = team, ktorému model dáva väčšiu šancu na výhru. Prstenec okolo teamu = Pulse (forma 0 – 100) vo farbe úrovne.",
    empty: "Žiadne naplánované zápasy v najbližších dňoch.",
  });
}
