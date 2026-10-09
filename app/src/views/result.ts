/* Výsledky: dohrané zápasy po dňoch v našom čase, náš tip (nevyšiel = celý červený) a štatistiky hráčov. */
import type { AppData, BoxRow, Result } from "../data";
import { coin, dayHeading, esc, groupBy, header, localDay, longDate, parseUtc, split, TEAM_NAMES, time } from "../ui";
import { isPre } from "./games";

const COLS: [keyof BoxRow, string, string][] = [
  ["min", "MIN", "minúty"],
  ["pts", "B", "body"],
  ["reb", "D", "doskoky"],
  ["ast", "A", "asistencie"],
  ["blk", "BL", "bloky"],
];
const SHOWN = 8; // hráči s najviac minútami, ostatní po rozkliknutí

/* Náš tip pred zápasom: favorit modelu a či vyhral. null = predpoveď sa neuložila. */
export function tipResult(r: Result): { fav: string; p: number; hit: boolean } | null {
  if (r.p_home == null) return null;
  const { home, away } = split(r.p_home);
  const homeFav = r.p_home > 0.5; // rovnako ako vo vyhodnotení modelu
  return { fav: homeFav ? r.home : r.away, p: homeFav ? home : away, hit: homeFav === r.pts_home > r.pts_away };
}

const resultClass = (r: Result): string => {
  const t = tipResult(r);
  return t ? (t.hit ? "hit" : "miss") : "none";
};

function verdict(r: Result): string {
  const t = tipResult(r);
  if (!t) return `<p class="tipline muted">Tip pred zápasom sa neuložil</p>`;
  return `<p class="tipline">Tip ${esc(t.fav)} ${t.p} % · <b>${t.hit ? "vyšiel" : "nevyšiel"}</b></p>`;
}

export function resultRow(r: Result): string {
  const homeWon = r.pts_home > r.pts_away;
  const line = (team: string, pts: number, won: boolean, home: boolean) => `<div class="tl${won ? " won" : ""}">
      ${coin(team)}<span class="abbr">${esc(team)}</span>${home ? `<span class="home">doma</span>` : ""}<span class="val">${pts}</span></div>`;
  return `<li><a class="match result ${resultClass(r)}" href="#/vysledok/${esc(r.game_id)}">
    <div class="when"><span class="clock">${time(r.tipoff_utc)}</span>${isPre(r) ? `<span class="tag">príprava</span>` : ""}</div>
    <div class="teams">${line(r.away, r.pts_away, !homeWon, false)}${line(r.home, r.pts_home, homeWon, true)}</div>
    ${verdict(r)}
  </a></li>`;
}

const byNewest = (a: Result, b: Result): number =>
  (parseUtc(b.tipoff_utc)?.getTime() ?? 0) - (parseUtc(a.tipoff_utc)?.getTime() ?? 0) || b.date.localeCompare(a.date) || b.game_id.localeCompare(a.game_id);

export function resultsView(d: AppData): string {
  const results = [...(d.predictions.results ?? [])].sort(byNewest);
  if (!results.length) return `${header("Výsledky")}<p class="empty">Zatiaľ žiadne dohrané zápasy. Výsledky sa objavia po skončení prvých zápasov.</p>`;
  const tips = results.map(tipResult).filter((t) => t !== null);
  const hits = tips.filter((t) => t.hit).length;
  const days = groupBy(results, (r) => localDay(r.tipoff_utc, r.date));
  return `${header("Výsledky", tips.length ? `tipy vyšli v <b>${hits} z ${tips.length}</b> zápasov` : "")}
    ${days.map(([day, rs]) => `<section>${dayHeading(day, rs.length, ["zápas", "zápasy", "zápasov"])}<ul class="list">${rs.map(resultRow).join("")}</ul></section>`).join("")}
    <p class="meta">Červený zápas = náš tip nevyšiel. Tip je posledná predpoveď modelu uložená pred začiatkom zápasu.</p>`;
}

function rowsOf(rows: BoxRow[]): string {
  return rows.map((p) => `<tr><td class="p">${esc(p.player)}</td>${COLS.map(([k]) => `<td class="n">${p[k]}</td>`).join("")}</tr>`).join("");
}

function boxTable(team: string, rows: BoxRow[], won: boolean): string {
  const head = COLS.map(([, short, long]) => `<th class="n" scope="col"><abbr title="${long}">${short}</abbr></th>`).join("");
  const rest = rows.slice(SHOWN);
  return `<h2 class="sec">${esc(TEAM_NAMES[team] ?? team)}${won ? ` <span class="won-tag">víťaz</span>` : ""}</h2>
    <section class="card flush"><table class="table box"><caption class="sr-only">Štatistiky hráčov ${esc(TEAM_NAMES[team] ?? team)}</caption>
    <thead><tr><th scope="col">Hráč</th>${head}</tr></thead><tbody>${rowsOf(rows.slice(0, SHOWN))}</tbody></table>
    ${rest.length ? `<details class="more inner"><summary>Ďalší hráči (${rest.length})</summary><table class="table box"><caption class="sr-only">Ďalší hráči ${esc(team)}</caption><thead class="sr-only"><tr><th scope="col">Hráč</th>${head}</tr></thead><tbody>${rowsOf(rest)}</tbody></table></details>` : ""}
    </section>`;
}

export function resultView(d: AppData, id: string): string {
  const r = (d.predictions.results ?? []).find((x) => x.game_id === id);
  const back = { href: "#/vysledky", label: "Výsledky" };
  if (!r) return `${header("Výsledok sa nenašiel", "", back)}<p class="empty">Výsledok už nie je medzi poslednými zápasmi. <a href="#/vysledky">Späť na výsledky</a></p>`;
  const homeWon = r.pts_home > r.pts_away;
  const t = tipResult(r);
  const day = longDate(localDay(r.tipoff_utc, r.date));
  const teams = [r.away, r.home];
  const box = teams.every((x) => r.box[x]?.length)
    ? teams.map((x) => boxTable(x, r.box[x], x === (homeWon ? r.home : r.away))).join("")
    : `<p class="empty">Štatistiky hráčov zatiaľ nie sú, doplnia sa pri ďalšej aktualizácii.</p>`;
  return `${header(`${esc(r.away)} <span class="at">@</span> ${esc(r.home)}`, `${esc(day)}${time(r.tipoff_utc) ? `, ${time(r.tipoff_utc)}` : ""}${isPre(r) ? " · príprava" : ""}`, back)}
    <section class="card hero score ${resultClass(r)}">
      <div class="duel">
        <div class="side${!homeWon ? " won" : ""}">${coin(r.away, true)}<a class="tname" href="#/team/${esc(r.away)}">${esc(TEAM_NAMES[r.away] ?? r.away)}</a><span class="small muted">hostia</span><span class="pct num">${r.pts_away}</span></div>
        <div class="side${homeWon ? " won" : ""}">${coin(r.home, true)}<a class="tname" href="#/team/${esc(r.home)}">${esc(TEAM_NAMES[r.home] ?? r.home)}</a><span class="small muted">doma</span><span class="pct num">${r.pts_home}</span></div>
      </div>
      <p class="verdict">${t ? `Náš tip pred zápasom: <b>${esc(t.fav)} ${t.p} %</b> · <b class="${t.hit ? "pos" : "neg"}">${t.hit ? "vyšiel" : "nevyšiel"}</b>` : "Tip pred týmto zápasom sa neuložil."}</p>
    </section>
    ${box}
    <p class="meta">MIN minúty · B body · D doskoky · A asistencie · BL bloky</p>`;
}
