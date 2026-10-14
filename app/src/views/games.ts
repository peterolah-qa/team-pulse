/* Zápasy: najbližšie zápasy po dňoch v našom čase. Jeden zápas = hostia a domáci pod sebou, vpravo šanca. */
import type { AppData, Sport } from "../data";
import { allGames } from "../data";
import { coin, dayHeading, esc, groupBy, header, localDay, oddsBar, parseUtc, split, time, when } from "../ui";

/* Čo riadok zápasu potrebuje – spĺňa NBA aj NHL zápas. */
interface Side {
  team: string;
  reasons: [string, number][];
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

function line(s: Side, p: number, fav: boolean, home: boolean, sport: Sport): string {
  return `<div class="tl${fav ? " fav" : ""}">
      ${coin(s.team, false, sport)}<span class="abbr">${esc(s.team)}</span>${home ? `<span class="home">doma</span>` : ""}
      ${fav ? `<span class="tip">tip</span>` : ""}
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
  return `<li><a class="match" href="#/${sport === "nhl" ? "nhl/" : ""}zapas/${esc(g.game_id)}">
    <div class="when"><span class="clock">${time(g.tipoff_utc)}</span>${liveTag(g, now)}${isPre(g) ? `<span class="tag">príprava</span>` : ""}</div>
    <div class="teams">${line(g.away, away, !homeFav, false, sport)}${line(g.home, home, homeFav, !g.neutral, sport)}${oddsBar(g.p_home)}</div>
    ${notes.length || g.neutral ? `<p class="note">${[g.neutral ? "neutrálne ihrisko" : "", ...notes].filter(Boolean).map(esc).join(" · ")}</p>` : ""}
  </a></li>`;
}

export function byTipoff<T extends { tipoff_utc?: string; game_id: string }>(a: T, b: T): number {
  const ta = parseUtc(a.tipoff_utc)?.getTime() ?? 0, tb = parseUtc(b.tipoff_utc)?.getTime() ?? 0;
  return ta - tb || a.game_id.localeCompare(b.game_id);
}

export function gamesView(d: AppData): string {
  const p = d.predictions;
  const finished = new Set((p.results ?? []).map((r) => r.game_id)); // dohrané sú už vo Výsledkoch
  const games = allGames(p).filter((g) => !finished.has(g.game_id)).sort(byTipoff);
  const now = Date.now();
  const days = groupBy(games, (g) => localDay(g.tipoff_utc, g.date));
  const body = days.length
    ? days.map(([day, gs]) => `<section>${dayHeading(day, gs.length, ["zápas", "zápasy", "zápasov"])}<ul class="list">${gs.map((g) => gameRow(g, now)).join("")}</ul></section>`).join("")
    : `<p class="empty">Žiadne naplánované zápasy v najbližších dňoch.</p>`;
  return `${header("Zápasy", `aktualizované ${esc(when(p.generated_at))}`)}
    ${body}
    <p class="meta">Časy sú v našom čase. Tip = team, ktorému model dáva väčšiu šancu na výhru.</p>`;
}
