/* Tipy: favoriti zápasov, ktoré ešte nezačali, zoradení od najväčšej šance modelu nadol.
   Pri každom riadku je aj šanca, že vyjdú všetky tipy od prvého po tento (šance sa násobia). */
import type { AppData, Game } from "../data";
import { allGames } from "../data";
import { esc, header, localDay, parseUtc, shortDate, split, time, when } from "../ui";
import { isPre } from "./games";

export interface Tip {
  game: Game;
  team: string;
  opp: string;
  home: boolean;
  p: number; // šanca favorita podľa modelu (0,5 – 1)
}

/* Favorit každého zápasu, ktorý ešte nezačal a nie je dohraný; zoradené podľa šance, pri zhode skorší zápas. */
export function tips(d: AppData, now: number = Date.now()): Tip[] {
  const finished = new Set((d.predictions.results ?? []).map((r) => r.game_id));
  return allGames(d.predictions)
    .filter((g) => !finished.has(g.game_id) && (parseUtc(g.tipoff_utc)?.getTime() ?? Infinity) > now)
    .map((g) => {
      const home = g.p_home > 0.5; // rovnako ako vo vyhodnotení: presne 50 % = tip na hostí
      return { game: g, team: home ? g.home.team : g.away.team, opp: home ? g.away.team : g.home.team, home, p: home ? g.p_home : 1 - g.p_home };
    })
    .sort((a, b) => b.p - a.p || (parseUtc(a.game.tipoff_utc)?.getTime() ?? 0) - (parseUtc(b.game.tipoff_utc)?.getTime() ?? 0));
}

export function tipsView(d: AppData): string {
  const list = tips(d);
  if (!list.length) return `${header("Tipy")}<p class="empty">Žiadne zápasy, ktoré ešte nezačali. Tipy sa objavia s ďalším rozpisom.</p>`;
  let all = 1;
  const rows = list.map((t, i) => {
    all *= t.p;
    const g = t.game;
    const where = g.neutral ? "proti" : t.home ? "doma s" : "@";
    return `<li><a class="tiprow" href="#/zapas/${esc(g.game_id)}">
      <span class="rank num">${i + 1}</span>
      <span class="tipmain"><span class="abbr">${esc(t.team)}</span> <span class="muted">${where} ${esc(t.opp)}</span>
        <span class="tipmeta">${esc(shortDate(localDay(g.tipoff_utc, g.date)))} ${time(g.tipoff_utc)}${isPre(g) ? ` <span class="tag">príprava</span>` : ""}</span></span>
      <span class="tipp num">${t.home ? split(g.p_home).home : split(g.p_home).away} %</span>
      ${i ? `<span class="acc">tipy 1 – ${i + 1} spolu: <b class="num">${Math.round(all * 100)} %</b></span>` : `<span class="acc">najistejší tip</span>`}
    </a></li>`;
  });
  return `${header("Tipy", `aktualizované ${esc(when(d.predictions.generated_at))}`)}
    <p class="hint lead">Favoriti zápasov, ktoré ešte nezačali, od najväčšej šance podľa modelu. „Spolu“ je šanca, že vyjdú všetky tipy od prvého po daný riadok.</p>
    <ul class="list">${rows.join("")}</ul>
    <p class="meta">Šance tipov sa násobia, takže každý ďalší zápas celkovú šancu zníži. Percentá sú z modelu, nie od stávkových kancelárií; naostro ich overí brána G2 (20. 10. – 3. 11.).</p>`;
}
