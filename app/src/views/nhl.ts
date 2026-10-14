/* NHL (beta): zápasy, tipy, výsledky, liga podľa Ela a model. Tipy sa zamykajú raz ráno (Mac),
   appka ich len ukazuje. Bez súpisiek a štatistík hráčov – tie NHL zatiaľ nemá. */
import type { NhlData, NhlGame, NhlResult, NhlSide } from "../data";
import { coin, dayHeading, esc, groupBy, header, localDay, longDate, signed, split, teamName, time, when } from "../ui";
import { byTipoff, gameRow, isPre } from "./games";
import { modelPage } from "./model";
import { recentOf } from "./result";
import { tipsFrom, tipsPage } from "./tips";

const BASE = "#/nhl/";
const EXTRA: Record<string, string> = { OT: "pp", SO: "sn" }; // po predĺžení, po samostatných nájazdoch

const beta = (): string =>
  `<p class="hint beta-note"><span class="beta">beta</span> NHL je nová. Model Elo + únava sa ostro overuje do 26. 10., tipy sa zamykajú raz ráno.</p>`;

const games = (n: NhlData): NhlGame[] => Object.values(n.predictions.days).flat();
const finished = (n: NhlData): Set<string> => new Set(n.predictions.results.map((r) => r.game_id));
const updated = (n: NhlData): string =>
  `tipy z ${esc(when(n.predictions.last_locked ?? n.predictions.generated_at))} · výsledky ${esc(when(n.predictions.generated_at))}`;

/* Poznámka pod zápasom: najväčší vplyv únavy na každý team („DET: back-to-back“). */
const fatigue = (g: NhlGame): string[] => [g.away, g.home].flatMap((s) => (s.reasons.length ? [`${s.team}: ${s.reasons[0][0]}`] : []));

export function nhlGamesView(n: NhlData): string {
  const done = finished(n);
  const list = games(n).filter((g) => !done.has(g.game_id)).sort(byTipoff);
  const now = Date.now();
  const days = groupBy(list, (g) => localDay(g.tipoff_utc, g.date));
  const body = days.length
    ? days
        .map(([day, gs]) => `<section>${dayHeading(day, gs.length, ["zápas", "zápasy", "zápasov"])}<ul class="list">${gs
          .map((g) => gameRow(g, now, { sport: "nhl", notes: fatigue(g) }))
          .join("")}</ul></section>`)
        .join("")
    : `<p class="empty">Žiadne zápasy s tipom. Tipy na ďalšie dni pribudnú ráno.</p>`;
  return `${header("Zápasy", updated(n))}${beta()}${body}
    <p class="meta">Časy sú v našom čase. Tip = team, ktorému model dáva väčšiu šancu na výhru (aj po predĺžení alebo nájazdoch).</p>`;
}

export function nhlTipsView(n: NhlData): string {
  const list = tipsFrom(games(n), finished(n));
  if (!list.length) return `${header("Tipy")}${beta()}<p class="empty">Žiadne zápasy, ktoré ešte nezačali. Tipy pribudnú ráno.</p>`;
  return tipsPage(
    list,
    n.predictions.last_locked ?? n.predictions.generated_at,
    "nhl",
    "Hokej je náhodnejší než basketbal, aj silný favorit často prehrá. Percentá sú z modelu, nie od stávkových kancelárií; naostro ich overuje brána G2-NHL (13. – 26. 10.).",
    beta(),
  );
}

/* Náš tip pred zápasom: favorit modelu a či vyhral (rovnaké pravidlo ako pri NBA). */
function tipOf(r: NhlResult): { fav: string; p: number; hit: boolean } | null {
  if (r.p_home == null) return null;
  const { home, away } = split(r.p_home);
  const homeFav = r.p_home > 0.5;
  return { fav: homeFav ? r.home : r.away, p: homeFav ? home : away, hit: homeFav === r.goals_home > r.goals_away };
}

function resultRow(r: NhlResult): string {
  const homeWon = r.goals_home > r.goals_away;
  const t = tipOf(r);
  const extra = r.last_period && EXTRA[r.last_period] ? ` <span class="tag">${EXTRA[r.last_period]}</span>` : "";
  const line = (team: string, goals: number, won: boolean, home: boolean) => `<div class="tl${won ? " won" : ""}">
      ${coin(team, false, "nhl")}<span class="abbr">${esc(team)}</span>${home ? `<span class="home">doma</span>` : ""}<span class="val">${goals}</span></div>`;
  return `<li><div class="match result ${t ? (t.hit ? "hit" : "miss") : "none"}">
    <div class="when"><span class="clock">${time(r.tipoff_utc)}</span>${extra}</div>
    <div class="teams">${line(r.away, r.goals_away, !homeWon, false)}${line(r.home, r.goals_home, homeWon, true)}</div>
    ${t ? `<p class="tipline">Tip ${esc(t.fav)} ${t.p} % · <b>${t.hit ? "vyšiel" : "nevyšiel"}</b></p>` : `<p class="tipline muted">Tip pred zápasom sa neuložil</p>`}
  </div></li>`;
}

export function nhlResultsView(n: NhlData): string {
  const results = recentOf(n.predictions.results);
  if (!results.length) return `${header("Výsledky")}${beta()}<p class="empty">Včera ani dnes sa ešte nedohral žiadny zápas NHL.</p>`;
  const tips = results.map(tipOf).filter((t) => t !== null);
  const hits = tips.filter((t) => t.hit).length;
  const days = groupBy(results, (r) => localDay(r.tipoff_utc, r.date));
  return `${header("Výsledky", tips.length ? `tipy vyšli v <b>${hits} z ${tips.length}</b> zápasov` : "")}${beta()}
    ${days.map(([day, rs]) => `<section>${dayHeading(day, rs.length, ["zápas", "zápasy", "zápasov"])}<ul class="list">${rs.map(resultRow).join("")}</ul></section>`).join("")}
    <p class="meta">Výsledky zo včera a z dneška. pp = po predĺžení, sn = po nájazdoch. Červený zápas = náš tip nevyšiel.</p>`;
}

function why(n: NhlData, g: NhlGame): string {
  const diff = Math.round(g.home.elo - g.away.elo);
  const stronger = diff >= 0 ? g.home.team : g.away.team;
  const rows: string[] = [
    `<li><span><b>${esc(stronger)}</b> silnejší (Elo ${Math.round(Math.max(g.home.elo, g.away.elo))} : ${Math.round(Math.min(g.home.elo, g.away.elo))})</span><span class="pos">pomáha <span class="num">${signed(Math.abs(diff))}</span></span></li>`,
  ];
  const hca = Math.round(n.model.elo_weights.home ?? 0);
  if (!g.neutral && hca) rows.push(`<li><span><b>${esc(g.home.team)}</b> domáce prostredie</span><span class="pos">pomáha <span class="num">${signed(hca)}</span></span></li>`);
  const side = (s: NhlSide) =>
    s.reasons.map(([t, e]) => `<li><span><b>${esc(s.team)}</b> ${esc(t)}</span><span class="${e >= 0 ? "pos" : "neg"}">${e >= 0 ? "pomáha" : "oslabuje"} <span class="num">${signed(e)}</span></span></li>`);
  rows.push(...side(g.away), ...side(g.home));
  return `<ul class="rows">${rows.join("")}</ul>`;
}

export function nhlGameView(n: NhlData, id: string): string {
  const back = { href: BASE, label: "Zápasy" };
  const g = games(n).find((x) => x.game_id === id);
  if (!g) return `${header("Zápas sa nenašiel", "", back)}<p class="empty">Tento zápas už nie je medzi tipmi. <a href="${BASE}">Späť na zápasy</a></p>`;
  const { home, away } = split(g.p_home);
  const homeFav = g.p_home > 0.5;
  const fav = homeFav ? g.home : g.away;
  const day = longDate(localDay(g.tipoff_utc, g.date));
  const side = (s: NhlSide, p: number, isFav: boolean, where: string) => `<div class="side${isFav ? " fav" : ""}">
      ${coin(s.team, true, "nhl")}<span class="tname">${esc(teamName(s.team, "nhl"))}</span>
      <span class="small muted">${where}</span>
      <span class="pct num">${p} %</span>${isFav ? `<span class="tip">tip</span>` : ""}</div>`;
  return `${header(`${esc(g.away.team)} <span class="at">@</span> ${esc(g.home.team)}`, `${esc(day)}, ${time(g.tipoff_utc)}${isPre(g) ? " · príprava" : ""}${g.neutral ? " · neutrálne ihrisko" : ""}`, back)}
    <section class="card hero">
      <div class="duel">${side(g.away, away, !homeFav, "hostia")}${side(g.home, home, homeFav, g.neutral ? "neutrálne" : "doma")}</div>
      <div class="bar ${homeFav ? "home-fav" : "away-fav"}" role="img" aria-label="Šanca na výhru: ${esc(g.away.team)} ${away} %, ${esc(g.home.team)} ${home} %"><i style="width:${away}%"></i></div>
      <p class="verdict">Tip: <b>${esc(fav.team)}</b> vyhrá so šancou ${homeFav ? home : away} % (aj po predĺžení alebo nájazdoch).</p>
    </section>
    ${beta()}
    <h2 class="sec">Prečo</h2><section class="card">${why(n, g)}
      <p class="small muted">Vplyv v Elo bodoch. Únava: zápas deň po dni, 3. zápas za 4 dni, cestovanie na východ, dlhý výjazd.</p></section>
    <p class="meta">Tip zamknutý ${esc(when(g.locked_at))}. Po začiatku zápasu sa už nemení.</p>`;
}

export function nhlTeamsView(n: NhlData): string {
  const list = n.predictions.teams;
  if (!list.length) return `${header("Teamy")}${beta()}<p class="empty">Zatiaľ žiadne teamy s tipom.</p>`;
  const elos = list.map((t) => t.elo);
  const lo = Math.min(...elos) - 20, hi = Math.max(...elos);
  const rows = list
    .map((t, i) => `<li><div class="teamrow">
      <span class="rank num">${i + 1}</span><span class="abbr">${coin(t.team, false, "nhl")}${esc(t.team)}</span><span class="name">${esc(teamName(t.team, "nhl"))}</span>
      <span class="meter elo" aria-hidden="true"><i style="width:${(((t.elo - lo) / (hi - lo)) * 100).toFixed(0)}%"></i></span>
      <span class="pulse num elo">${Math.round(t.elo)}</span></div></li>`)
    .join("");
  return `${header("Teamy", "sila podľa výsledkov (Elo), od najsilnejšieho")}${beta()}
    <section><h2 class="day"><span>Liga podľa Ela</span><span class="day-n">${list.length}</span></h2><ul class="list tight">${rows}</ul></section>
    <p class="meta">Elo pred posledným zápasom s tipom, priemer ligy je 1505. Forma (Pulse), súpisky a zranenia zatiaľ len pri NBA.</p>`;
}

const NHL_WEIGHTS: Record<string, string> = {
  home: "Domáce prostredie",
  home_b2b: "Domáci: 2. zápas za 2 dni",
  away_b2b: "Hostia: 2. zápas za 2 dni",
  home_three_in4: "Domáci: 3. zápas za 4 dni",
  away_three_in4: "Hostia: 3. zápas za 4 dni",
  home_rest: "Domáci: každý deň voľna navyše",
  away_rest: "Hostia: každý deň voľna navyše",
  home_tz_east: "Domáci: posun na východ (1 h)",
  away_tz_east: "Hostia: posun na východ (1 h)",
  away_road: "Hostia: každý ďalší zápas výjazdu",
};

export function nhlModelView(n: NhlData): string {
  return modelPage(n.model, NHL_WEIGHTS, "Hokej je náhodnejší než basketbal: tip „vždy domáci“ trafí v tých istých sezónach 54,3 %.", beta());
}
