/* Tipy: favoriti zápasov, ktoré ešte nezačali, zoradení od najväčšej šance modelu nadol.
   Pri každom riadku je aj šanca, že vyjdú všetky tipy od prvého po tento (šance sa násobia) – aj ako graf. */
import type { AppData, Sport } from "../data";
import { allGames } from "../data";
import { coin, esc, header, localDay, parseUtc, shortDate, split, time, when } from "../ui";
import { isPre, type RowGame } from "./games";

export interface Tip {
  game: RowGame;
  team: string;
  opp: string;
  home: boolean;
  p: number; // šanca favorita podľa modelu (0,5 – 1)
}

/* Favorit každého zápasu, ktorý ešte nezačal a nie je dohraný; zoradené podľa šance, pri zhode skorší zápas. */
export function tipsFrom(games: RowGame[], finished: Set<string>, now: number = Date.now()): Tip[] {
  return games
    .filter((g) => !finished.has(g.game_id) && (parseUtc(g.tipoff_utc)?.getTime() ?? Infinity) > now)
    .map((g) => {
      const home = g.p_home > 0.5; // rovnako ako vo vyhodnotení: presne 50 % = tip na hostí
      return { game: g, team: home ? g.home.team : g.away.team, opp: home ? g.away.team : g.home.team, home, p: home ? g.p_home : 1 - g.p_home };
    })
    .sort((a, b) => b.p - a.p || (parseUtc(a.game.tipoff_utc)?.getTime() ?? 0) - (parseUtc(b.game.tipoff_utc)?.getTime() ?? 0));
}

export function tips(d: AppData, now: number = Date.now()): Tip[] {
  return tipsFrom(allGames(d.predictions), new Set((d.predictions.results ?? []).map((r) => r.game_id)), now);
}

/* Spolu = súčin šancí prvých k tipov, v celých percentách (rovnaké číslo ako v riadkoch). */
function together(list: Tip[]): number[] {
  let all = 1;
  return list.map((t) => Math.round((all *= t.p) * 100));
}

/* Graf: ako klesá šanca, že vyjdú všetky tipy, keď ich pridávam. Jedna čiara, popis prvého a posledného bodu. */
function chart(acc: number[]): string {
  if (acc.length < 2) return "";
  const W = 320, H = 150, padL = 44, padR = 16, padT = 16, padB = 26;
  const x = (i: number) => padL + (i / (acc.length - 1)) * (W - padL - padR);
  const y = (v: number) => padT + (1 - v / 100) * (H - padT - padB);
  const grid = [0, 25, 50, 75, 100]
    .map((v) => `<line x1="${padL}" x2="${W - padR}" y1="${y(v)}" y2="${y(v)}" class="grid"/><text x="${padL - 6}" y="${y(v) + 4}" text-anchor="end" class="axis-lbl">${v} %</text>`)
    .join("");
  const xt = acc.map((_, i) => `<text x="${x(i).toFixed(1)}" y="${H - 8}" text-anchor="middle" class="axis-lbl">${i + 1}</text>`).join("");
  const pts = acc.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const dots = acc
    .map((v, i) => `<g><circle cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}" r="11" class="hit"/><circle cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}" r="4" class="dot"/><title>${i ? `tipy 1 – ${i + 1} spolu` : "tip 1"}: ${v} %</title></g>`)
    .join("");
  const last = acc.length - 1;
  const lbl = (i: number, anchor: string, dx: number) =>
    `<text x="${(x(i) + dx).toFixed(1)}" y="${(y(acc[i]) - 10).toFixed(1)}" text-anchor="${anchor}" class="val-lbl">${acc[i]} %</text>`;
  const words = acc.map((v, i) => `${i + 1} ${i ? (i < 4 ? "tipy" : "tipov") : "tip"} ${v} %`).join(", ");
  return `<section class="card chart"><h2 class="chart-h">Šanca, že vyjdú všetky</h2>
    <svg class="cal acc-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Šanca, že vyjdú všetky tipy od prvého: ${esc(words)}">
      ${grid}${xt}<polyline points="${pts}" class="trend"/>${dots}${lbl(0, "start", 6)}${lbl(last, "end", -6)}</svg>
    <p class="small muted">Vodorovne: koľko tipov od najistejšieho. Zvislo: šanca, že vyjdú všetky naraz.</p></section>`;
}

export function tipsPage(list: Tip[], generatedAt: string, sport: Sport, footer: string, intro = ""): string {
  const base = sport === "nhl" ? "#/nhl/" : "#/";
  const acc = together(list);
  const rows = list.map((t, i) => {
    const g = t.game;
    const where = g.neutral ? "proti" : t.home ? "doma s" : "@";
    return `<li><a class="tiprow" href="${base}zapas/${esc(g.game_id)}">
      <span class="rank num">${i + 1}</span>
      <span class="tipmain">${coin(t.team, false, sport)}<span class="abbr">${esc(t.team)}</span> <span class="muted">${where} ${esc(t.opp)}</span>
        <span class="tipmeta">${esc(shortDate(localDay(g.tipoff_utc, g.date)))} ${time(g.tipoff_utc)}${isPre(g) ? ` <span class="tag">príprava</span>` : ""}</span></span>
      <span class="tipp num">${t.home ? split(g.p_home).home : split(g.p_home).away} %</span>
      ${i ? `<span class="acc">tipy 1 – ${i + 1} spolu: <b class="num">${acc[i]} %</b></span>` : `<span class="acc">najistejší tip</span>`}
    </a></li>`;
  });
  return `${header("Tipy", `aktualizované ${esc(when(generatedAt))}`)}${intro}
    <div class="split">
      <div class="split-side">
        <p class="hint lead">Favoriti zápasov, ktoré ešte nezačali, od najväčšej šance podľa modelu. „Spolu“ je šanca, že vyjdú všetky tipy od prvého po daný riadok.</p>
        ${chart(acc)}
      </div>
      <ul class="list split-main">${rows.join("")}</ul>
    </div>
    <p class="meta">${footer}</p>`;
}

export function tipsView(d: AppData): string {
  const list = tips(d);
  if (!list.length) return `${header("Tipy")}<p class="empty">Žiadne zápasy, ktoré ešte nezačali. Tipy sa objavia s ďalším rozpisom.</p>`;
  return tipsPage(
    list,
    d.predictions.generated_at,
    "nba",
    "Šance tipov sa násobia, takže každý ďalší zápas celkovú šancu zníži. Percentá sú z modelu, nie od stávkových kancelárií; naostro ich overí brána G2 (20. 10. – 3. 11.).",
  );
}
