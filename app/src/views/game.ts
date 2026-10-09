/* Detail zápasu: tip a šanca, prečo, čo ak otázny hráč nenastúpi, forma teamov, podrobnosti modelu. */
import type { AppData, Game, TeamState } from "../data";
import { allGames } from "../data";
import { chip, coin, esc, header, localDay, longDate, pulseNum, signed, split, TEAM_NAMES, time } from "../ui";
import { isPre } from "./games";

const LAYERS: [keyof NonNullable<TeamState["layers"]>, string][] = [
  ["strength", "Sila teamu"],
  ["roster", "Súpiska"],
  ["players", "Chýbajúci hráči"],
  ["fatigue", "Únava a cestovanie"],
];

function reasons(g: Game): string {
  const all = [g.away, g.home]
    .flatMap((s) => s.reasons.map(([t, e]) => ({ team: s.team, t, e })))
    .sort((a, b) => Math.abs(b.e) - Math.abs(a.e))
    .slice(0, 4);
  if (!all.length) return `<p class="muted">Žiadny výrazný faktor, rozhoduje najmä sila teamov.</p>`;
  return `<ul class="rows">${all
    .map((r) => `<li><span><b>${esc(r.team)}</b> ${esc(r.t)}</span><span class="${r.e >= 0 ? "pos" : "neg"}">${r.e >= 0 ? "pomáha" : "oslabuje"} <span class="num">${signed(r.e)}</span></span></li>`)
    .join("")}</ul>`;
}

function whatIf(g: Game): string {
  if (!g.what_if.length) return "";
  const homeNow = split(g.p_home).home;
  const rows = g.what_if.map((w) => {
    const out = split(w.out.p_home).home;
    const homeFav = g.p_home > 0.5;
    const fav = homeFav ? g.home.team : g.away.team;
    const now = homeFav ? homeNow : 100 - homeNow;
    const then = homeFav ? out : 100 - out;
    return `<li><span>Ak <b>${esc(w.player)}</b> (${esc(w.team)}) nenastúpi</span><span class="num">${esc(fav)} ${now} % → ${then} %</span></li>`;
  });
  return `<h2 class="sec">Otázni hráči</h2><ul class="rows card">${rows.join("")}</ul>`;
}

function points(margin: number): string {
  const n = Math.round(margin);
  if (n < 1) return "vyrovnaný zápas";
  return `očakávaný rozdiel asi ${n} ${n === 1 ? "bod" : n < 5 ? "body" : "bodov"}`;
}

function form(s: TeamState): string {
  return `<a class="formrow" href="#/team/${esc(s.team)}">
      ${coin(s.team)}<span class="abbr">${esc(s.team)}</span><span class="name">${esc(TEAM_NAMES[s.team] ?? s.team)}</span>
      <span class="pulse">Pulse <b class="num">${pulseNum(s.pulse)}</b></span>${chip(s.tier)}
      ${s.dropped ? `<span class="small muted">normálne ${esc(s.normal_tier)}</span>` : ""}<span class="chev" aria-hidden="true">›</span></a>`;
}

function details(g: Game): string {
  const rows = LAYERS.map(([k, label]) => [label, g.away.layers?.[k] ?? 0, g.home.layers?.[k] ?? 0] as const);
  rows.push(["Domáce prostredie", 0, g.home_adv]);
  const body = rows
    .filter(([, a, h]) => Math.round(a) !== 0 || Math.round(h) !== 0)
    .map(([label, a, h]) => `<tr><td>${label}</td><td class="n">${signed(Math.round(a))}</td><td class="n">${signed(Math.round(h))}</td></tr>`)
    .join("");
  return `<details class="more"><summary>Podrobnosti modelu</summary>
    <table class="table"><caption class="sr-only">Vplyv vrstiev modelu v Elo bodoch</caption>
      <thead><tr><th>Vplyv v Elo bodoch</th><th class="n">${esc(g.away.team)}</th><th class="n">${esc(g.home.team)}</th></tr></thead>
      <tbody>${body}</tbody></table>
    <p class="small muted">Sila teamu je odchýlka od priemeru ligy. Kladné číslo teamu pomáha, záporné ho oslabuje.</p></details>`;
}

export function gameView(d: AppData, id: string): string {
  const g = allGames(d.predictions).find((x) => x.game_id === id);
  if (!g) return `${header("Zápas sa nenašiel", "", { href: "#/", label: "Zápasy" })}<p class="empty">Tento zápas už nie je v predpovediach. <a href="#/">Späť na zápasy</a></p>`;
  const { home, away } = split(g.p_home);
  const homeFav = g.p_home > 0.5;
  const fav = homeFav ? g.home : g.away;
  const margin = Math.abs(g.margin_home);
  const day = longDate(localDay(g.tipoff_utc, g.date));
  const side = (s: TeamState, p: number, isFav: boolean, where: string) => `<div class="side${isFav ? " fav" : ""}">
      ${coin(s.team, true)}<a class="tname" href="#/team/${esc(s.team)}">${esc(TEAM_NAMES[s.team] ?? s.team)}</a>
      <span class="small muted">${where}</span>
      <span class="pct num">${p} %</span>${isFav ? `<span class="tip">tip</span>` : ""}</div>`;
  return `${header(`${esc(g.away.team)} <span class="at">@</span> ${esc(g.home.team)}`, `${esc(day)}, ${time(g.tipoff_utc)}${isPre(g) ? " · príprava" : ""}${g.neutral ? " · neutrálne ihrisko" : ""}`, { href: "#/", label: "Zápasy" })}
    <section class="card hero">
      <div class="duel">${side(g.away, away, !homeFav, "hostia")}${side(g.home, home, homeFav, g.neutral ? "neutrálne" : "doma")}</div>
      <div class="bar ${homeFav ? "home-fav" : "away-fav"}" role="img" aria-label="Šanca na výhru: ${esc(g.away.team)} ${away} %, ${esc(g.home.team)} ${home} %"><i style="width:${away}%"></i></div>
      <p class="verdict">Tip: <b>${esc(fav.team)}</b> vyhrá so šancou ${homeFav ? home : away} %, ${points(margin)}.</p>
    </section>
    ${isPre(g) ? `<p class="hint">Prípravný zápas: hviezdy hrajú menej a model je naučený na základnú časť, tip je len orientačný.</p>` : ""}
    <h2 class="sec">Prečo</h2><section class="card">${reasons(g)}</section>
    ${whatIf(g)}
    <h2 class="sec">Forma pred týmto zápasom</h2><section class="card">${form(g.away)}${form(g.home)}</section>
    ${details(g)}`;
}
