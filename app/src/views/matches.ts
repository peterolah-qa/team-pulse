/* Obrazovka Zápasy (NBA aj NHL): pás dní hore, zápasy ako balíček kariet (švih do strán) alebo zoznam,
   vedľa prehľad dňa. Na počítači sú karty v mriežke a prehľad v bočnom stĺpci. Všetky čísla sú z dát appky. */
import type { Sport } from "../data";
import { badge, dayHeading, dayTitle, esc, groupBy, header, localDay, type RingValue, shortDate, signed, signed1, split, time } from "../ui";
import { isPre, liveTag, type RowGame } from "./games";

export type Mode = "deck" | "list";
const MODE_KEY = "tp-mode";
const picked: Partial<Record<Sport, string>> = {}; // zvolený deň v pási (yyyy-mm-dd v našom čase)

export function mode(): Mode {
  try {
    return localStorage.getItem(MODE_KEY) === "list" ? "list" : "deck";
  } catch {
    return "deck";
  }
}

export function setMode(m: Mode): void {
  try {
    localStorage.setItem(MODE_KEY, m);
  } catch {
    /* bez úložiska ostane zobrazenie do zatvorenia appky */
  }
  memo = m;
}
let memo: Mode | null = null;
const current = (): Mode => memo ?? mode();

export function pickDay(sport: Sport, day: string): void {
  picked[sport] = day;
}

export const dayOf = (g: RowGame): string => localDay(g.tipoff_utc, g.date);

/* Favorit zápasu: rovnaké pravidlo ako vo vyhodnotení (presne 50 % = hostia). */
export function fav(g: RowGame): { team: string; p: number; home: boolean } {
  const home = g.p_home > 0.5;
  const { home: h, away: a } = split(g.p_home);
  return { team: home ? g.home.team : g.away.team, p: home ? h : a, home };
}

/* Šanca, že vyjdú všetky tipy z `gs` naraz (súčin), v celých percentách. */
export const together = (gs: RowGame[]): number => Math.round(gs.reduce((a, g) => a * Math.max(g.p_home, 1 - g.p_home), 1) * 100);

const plural = (n: number, w: [string, string, string]): string => (n === 1 ? w[0] : n >= 2 && n <= 4 ? w[1] : w[2]);

function chipLabel(day: string): { title: string; date: string } {
  const { title } = dayTitle(day);
  const short = shortDate(day);
  return ["Dnes", "Zajtra", "Včera"].includes(title) ? { title, date: short } : { title: short.split(" ")[0], date: short.split(" ").slice(1).join(" ") };
}

function strip(sport: Sport, days: [string, RowGame[]][], sel: string): string {
  const chips = days
    .map(([day, gs]) => {
      const top = gs.map(fav).sort((a, b) => b.p - a.p)[0];
      const { title, date } = chipLabel(day);
      const on = day === sel;
      return `<button type="button" class="dchip${on ? " on" : ""}" data-day="${day}" data-sport="${sport}" aria-pressed="${on}">
        <span class="dc-t">${esc(title)}</span><span class="dc-d">${esc(date)}</span>
        <span class="dc-n">${gs.length} ${plural(gs.length, ["zápas", "zápasy", "zápasov"])}</span>
        <span class="dc-tip">${esc(top.team)} <b class="num">${top.p} %</b></span></button>`;
    })
    .join("");
  return `<div class="dstrip" role="group" aria-label="Dni so zápasmi">${chips}</div>`;
}

function toolbar(m: Mode): string {
  const b = (id: Mode, label: string) => `<button type="button" data-mode="${id}" aria-pressed="${m === id}">${label}</button>`;
  return `<div class="toolbar"><div class="seg" role="group" aria-label="Zobrazenie zápasov">${b("deck", "Karty")}${b("list", "Zoznam")}</div></div>`;
}

/* Jedna strana karty: odznak s prstencom, skratka, celý názov, kde hrá, doplnkový riadok. */
export interface CardSide {
  ring?: RingValue;
  name: string;
  line?: string; // HTML: Pulse a úroveň (NBA), bilancia a Elo (NHL)
}

export interface CardData {
  href: string;
  away: CardSide;
  home: CardSide;
  reasons: [string, number][]; // [popis, vplyv v prospech tipu], najviac 4
  tone?: string; // farebný podtón karty podľa formy favorita (t0 – t3)
  venue?: string | null;
}

export function card(g: RowGame, sport: Sport, c: CardData, i: number, n: number, now: number): string {
  const { home, away } = split(g.p_home);
  const f = fav(g);
  const side = (s: "home" | "away", info: CardSide, p: number, isFav: boolean) => `<div class="mside${isFav ? " fav" : ""}${s === "home" ? " r" : ""}">
      ${badge(g[s].team, sport, "lg", info.ring)}
      <span class="ms-abbr">${esc(g[s].team)}</span><span class="ms-name">${esc(info.name)}</span>
      <span class="ms-where">${s === "home" ? (g.neutral ? "neutrálne" : "doma") : "hostia"}</span>
      ${info.line ? `<span class="ms-line">${info.line}</span>` : ""}
      <span class="ms-p num">${p} %</span></div>`;
  const whole = c.reasons.every(([, v]) => Number.isInteger(v)); // NBA celé Elo body, NHL rozpad na desatiny
  const reasons = c.reasons.length
    ? `<ul class="mreasons">${c.reasons
        .map(([t, v]) => `<li><span>${esc(t)}</span><span class="num ${v >= 0 ? "plus" : "minus"}">${whole ? signed(v) : signed1(v)}</span></li>`)
        .join("")}</ul>`
    : `<p class="small muted">Žiadny výrazný faktor, rozhoduje najmä sila teamov.</p>`;
  return `<li class="mcard${c.tone ? ` tone-${c.tone}` : ""}" aria-roledescription="karta" aria-label="Zápas ${i + 1} z ${n}: ${esc(g.away.team)} @ ${esc(g.home.team)}">
    <div class="mc-top"><span class="clock">${time(g.tipoff_utc)}</span>${liveTag(g, now)}${isPre(g) ? `<span class="tag">príprava</span>` : ""}${c.venue ? `<span class="mc-venue">${esc(c.venue)}</span>` : ""}</div>
    <div class="mduel">${side("away", c.away, away, !f.home)}<span class="mvs" aria-hidden="true">@</span>${side("home", c.home, home, f.home)}</div>
    <div class="bar tipbar ${f.home ? "home-fav" : "away-fav"}" role="img" aria-label="Šanca na výhru: ${esc(g.away.team)} ${away} %, ${esc(g.home.team)} ${home} %"><i style="width:${away}%"></i></div>
    <p class="mtip"><span class="tip">tip</span><b>${esc(f.team)}</b> vyhrá so šancou <b class="num">${f.p} %</b></p>
    <h3 class="label">Prečo ${esc(f.team)} <span class="muted">· Elo body v prospech tipu</span></h3>
    ${reasons}
    <a class="mc-more" href="${c.href}">Detail zápasu<span aria-hidden="true">›</span></a>
  </li>`;
}

function deck(cards: string[]): string {
  const n = cards.length;
  const segs = Array.from({ length: n }, (_, i) => `<i${i === 0 ? ' class="on"' : ""}></i>`).join("");
  return `<section class="deck" aria-roledescription="karusel" aria-label="Zápasy dňa">
    <div class="deck-top"><span class="deck-prog" aria-hidden="true">${segs}</span>
      <span class="deck-pos" aria-live="polite">Zápas 1 z ${n}</span>
      <span class="deck-nav"><button type="button" class="iconbtn sm" data-deck="-1" aria-label="Predchádzajúci zápas" disabled>‹</button><button type="button" class="iconbtn sm" data-deck="1" aria-label="Ďalší zápas"${n < 2 ? " disabled" : ""}>›</button></span></div>
    <ol class="deck-track" tabindex="0" aria-label="Karty zápasov, posúvaj do strán">${cards.join("")}</ol>
  </section>`;
}

export interface MatchesOpts {
  sport: Sport;
  games: RowGame[]; // nedohraté, zoradené podľa začiatku
  sub: string;
  intro?: string;
  card: (g: RowGame, i: number, n: number, now: number) => string;
  row: (g: RowGame, now: number) => string;
  widgets: (day: string, gs: RowGame[]) => string;
  footer: string;
  empty: string;
}

export function matchesPage(o: MatchesOpts): string {
  const now = Date.now();
  const days = groupBy(o.games, dayOf);
  if (!days.length) return `${header("Zápasy", o.sub)}${o.intro ?? ""}<p class="empty">${o.empty}</p>`;
  const sel = days.some(([d]) => d === picked[o.sport]) ? picked[o.sport]! : days[0][0];
  const dayGames = days.find(([d]) => d === sel)![1];
  const m = current();
  const main =
    m === "deck"
      ? deck(dayGames.map((g, i) => o.card(g, i, dayGames.length, now)))
      : days
          .map(([day, gs]) => `<section id="den-${day}">${dayHeading(day, gs.length, ["zápas", "zápasy", "zápasov"])}<ul class="list">${gs.map((g) => o.row(g, now)).join("")}</ul></section>`)
          .join("");
  return `${header("Zápasy", o.sub)}${o.intro ?? ""}
    ${strip(o.sport, days, sel)}${toolbar(m)}
    <div class="dash" data-view="${m}"><div class="dash-main">${main}</div>
      <aside class="dash-side" aria-label="Prehľad dňa">${o.widgets(sel, dayGames)}</aside></div>
    <p class="meta">${o.footer}</p>`;
}

/* --- widgety prehľadu dňa ------------------------------------------------------------------------- */

export function dayWidget(day: string, gs: RowGame[], sport: Sport): string {
  const base = sport === "nhl" ? "#/nhl/" : "#/";
  const tips = gs.map((g) => ({ g, ...fav(g) })).sort((a, b) => b.p - a.p);
  const top = tips[0];
  const avg = Math.round(tips.reduce((a, t) => a + t.p, 0) / tips.length);
  const { title, date } = dayTitle(day);
  return `<section class="card widget"><h2 class="label">${esc(title)}${date ? ` · ${esc(date)}` : ""}</h2>
    <div class="kpis">
      <div class="kpi"><span class="kpi-n num">${gs.length}</span><span class="kpi-l">${plural(gs.length, ["zápas", "zápasy", "zápasov"])}</span></div>
      <div class="kpi"><span class="kpi-n num">${avg} %</span><span class="kpi-l">priemerná šanca favorita</span></div>
      <div class="kpi"><span class="kpi-n num">${together(gs)} %</span><span class="kpi-l">všetky tipy dňa naraz</span></div>
    </div>
    <a class="toptip" href="${base}zapas/${esc(top.g.game_id)}">${badge(top.team, sport, "sm", { value: top.p, tone: "tip" })}
      <span><span class="label">Najistejší tip dňa</span><b>${esc(top.team)}</b> <span class="muted">${top.home ? "doma s" : "u"} ${esc(top.home ? top.g.away.team : top.g.home.team)}, ${time(top.g.tipoff_utc)}</span></span>
      <b class="num tipp">${top.p} %</b></a>
  </section>`;
}

/* Vplyvy z pohľadu tipu: [popis, Elo] → zoradené podľa veľkosti, najviac 4. */
export function topReasons(list: [string, number][], max = 4): [string, number][] {
  return [...list].sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, max);
}
