import type { AppData, BoxRow, Result } from "../data";
import { dayLabel, esc, header, pct, teamLink, TEAM_NAMES } from "../ui";

const COLS: [keyof BoxRow, string, string][] = [
  ["min", "MIN", "minúty"],
  ["pts", "B", "body"],
  ["reb", "D", "doskoky"],
  ["ast", "A", "asistencie"],
  ["blk", "BL", "bloky"],
  ["stl", "Z", "zisky"],
];

/* Náš tip pred zápasom: kto bol favorit a či vyhral. null = predpoveď sa neuložila. */
export function tipResult(r: Result): { fav: string; p: number; hit: boolean } | null {
  if (r.p_home == null) return null;
  const homeFav = r.p_home >= 0.5;
  return { fav: homeFav ? r.home : r.away, p: homeFav ? r.p_home : 1 - r.p_home, hit: homeFav === r.pts_home > r.pts_away };
}

export function tipMark(r: Result): string {
  const t = tipResult(r);
  if (!t) return `<span class="muted">tip neuložený</span>`;
  return `tip ${esc(t.fav)} ${pct(t.p)} <b class="${t.hit ? "hit" : "miss"}">${t.hit ? "✓" : "✗"}</b>`;
}

export function resultCard(r: Result): string {
  const homeWon = r.pts_home > r.pts_away;
  const line = (team: string, pts: number, won: boolean) =>
    `<div class="row team-row${won ? " won" : ""}"><span class="abbr">${esc(team)}</span><span class="num score">${pts}</span></div>`;
  return `<article class="card result" data-game="${esc(r.game_id)}">
    <a class="stretch" href="#/vysledok/${esc(r.game_id)}" aria-label="Výsledok ${esc(r.away)} na palubovke ${esc(r.home)}"></a>
    <div class="row small"><span>${esc(dayLabel(r.date))}${r.kind === "preseason" ? ` · <b class="pre">PRÍPRAVA</b>` : ""}</span><span>${tipMark(r)}</span></div>
    ${line(r.home, r.pts_home, homeWon)}${line(r.away, r.pts_away, !homeWon)}
  </article>`;
}

function boxTable(team: string, rows: BoxRow[]): string {
  const head = COLS.map(([, short, long]) => `<th class="n" scope="col"><abbr title="${long}">${short}</abbr></th>`).join("");
  const body = rows
    .map((p) => `<tr><td class="p">${esc(p.player)}</td>${COLS.map(([k]) => `<td class="n">${p[k]}</td>`).join("")}</tr>`)
    .join("");
  return `<h2 class="section">// ${esc(team)} · HRÁČI</h2>
    <section class="card"><table class="table box"><caption class="sr-only">Štatistiky hráčov ${esc(TEAM_NAMES[team] ?? team)}</caption>
    <thead><tr><th scope="col">Hráč</th>${head}</tr></thead><tbody>${body}</tbody></table></section>`;
}

export function resultView(d: AppData, id: string): string {
  const r = (d.predictions.results ?? []).find((x) => x.game_id === id);
  if (!r) return `${header("VÝSLEDOK", "NENÁJDENÝ")}<p class="empty">Výsledok sa nenašiel. <a href="#/">Späť na dnešné zápasy</a></p>`;
  const t = tipResult(r);
  const tip = t
    ? `Náš tip pred zápasom: <b>${esc(t.fav)} ${pct(t.p)}</b> · <b class="${t.hit ? "hit" : "miss"}">${t.hit ? "✓ trafený" : "✗ netrafený"}</b>`
    : "Predpoveď pred týmto zápasom sa neuložila.";
  const teams = [r.home, r.away];
  const box = teams.every((x) => r.box[x]?.length)
    ? teams.map((x) => boxTable(x, r.box[x])).join("")
    : `<p class="empty">${r.kind === "preseason" ? "Z prípravy máme len skóre, štatistiky hráčov nesťahujeme." : "Štatistiky hráčov zatiaľ nie sú, doplnia sa pri rannej aktualizácii."}</p>`;
  return `${header(`${dayLabel(r.date)} · VÝSLEDOK${r.kind === "preseason" ? " · PRÍPRAVA" : ""}`, `${teamLink(r.home)} <span class="num">${r.pts_home} : ${r.pts_away}</span> ${teamLink(r.away)}`, `doma<br>${esc(TEAM_NAMES[r.home] ?? r.home)}`)}
    <p class="small note">${tip}</p>
    ${box}
    <p class="meta">B body · D doskoky · A asistencie · BL bloky · Z zisky · zoradené podľa minút</p>`;
}
