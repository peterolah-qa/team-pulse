/* Tipy: favoriti zápasov, ktoré ešte nezačali, zoradení od najväčšej šance modelu nadol.
   Pri každom riadku je aj šanca, že vyjdú všetky tipy od prvého po tento (šance sa násobia) – aj ako graf. */
import type { AppData, Sport } from "../data";
import { allGames } from "../data";
import { badge, esc, header, localDay, parseUtc, shortDate, split, time, when } from "../ui";
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

/* Graf: stĺpce = šanca jednotlivého tipu, čiara s plochou = šanca, že vyjdú všetky od prvého po daný.
   Popis prvého a posledného bodu, ostatné v nápovede a v popise pre čítačky. */
function chart(acc: number[], ps: number[]): string {
  if (acc.length < 2) return "";
  const W = 320, H = 160, padL = 40, padR = 14, padT = 18, padB = 26;
  const step = (W - padL - padR) / acc.length;
  const x = (i: number) => padL + step * (i + 0.5);
  const y = (v: number) => padT + (1 - v / 100) * (H - padT - padB);
  const grid = [0, 25, 50, 75, 100]
    .map((v) => `<line x1="${padL}" x2="${W - padR}" y1="${y(v)}" y2="${y(v)}" class="grid"/><text x="${padL - 6}" y="${y(v) + 4}" text-anchor="end" class="axis-lbl">${v} %</text>`)
    .join("");
  const bw = Math.min(18, step * 0.55);
  const bars = ps.map((p, i) => `<rect x="${(x(i) - bw / 2).toFixed(1)}" y="${y(p).toFixed(1)}" width="${bw.toFixed(1)}" height="${(y(0) - y(p)).toFixed(1)}" rx="3" class="pbar"/>`).join("");
  const xt = acc.map((_, i) => `<text x="${x(i).toFixed(1)}" y="${H - 8}" text-anchor="middle" class="axis-lbl">${i + 1}</text>`).join("");
  const pts = acc.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const area = `${x(0).toFixed(1)},${y(0)} ${pts} ${x(acc.length - 1).toFixed(1)},${y(0)}`;
  const dots = acc
    .map((v, i) => `<g><circle cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}" r="11" class="hit"/><circle cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}" r="4" class="dot"/><title>${i ? `tipy 1 – ${i + 1} spolu` : "tip 1"}: ${v} %</title></g>`)
    .join("");
  const last = acc.length - 1;
  const lbl = (i: number, anchor: string, dx: number) =>
    `<text x="${(x(i) + dx).toFixed(1)}" y="${(y(acc[i]) - 10).toFixed(1)}" text-anchor="${anchor}" class="val-lbl">${acc[i]} %</text>`;
  const words = acc.map((v, i) => `${i + 1} ${i ? (i < 4 ? "tipy" : "tipov") : "tip"} ${v} %`).join(", ");
  return `<section class="card chart"><h2 class="label">Šanca, že vyjdú všetky</h2>
    <svg class="cal acc-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Šanca, že vyjdú všetky tipy od prvého: ${esc(words)}">
      <defs><linearGradient id="acc-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" class="af0"/><stop offset="1" class="af1"/></linearGradient></defs>
      ${grid}${bars}${xt}<polygon points="${area}" class="area" fill="url(#acc-fill)"/><polyline points="${pts}" class="trend"/>${dots}${lbl(0, "start", 6)}${lbl(last, "end", -6)}</svg>
    <p class="small muted">Stĺpec = šanca jedného tipu, čiara = všetky tipy od prvého po daný spolu. Šance sa násobia, preto čiara vždy klesá.</p></section>`;
}

export function tipsPage(list: Tip[], generatedAt: string, sport: Sport, footer: string, intro = ""): string {
  const base = sport === "nhl" ? "#/nhl/" : "#/";
  const acc = together(list);
  const ps = list.map((t) => (t.home ? split(t.game.p_home).home : split(t.game.p_home).away));
  const rows = list.map((t, i) => {
    const g = t.game;
    const where = g.neutral ? "proti" : t.home ? "doma s" : "@";
    return `<li><a class="tiprow" href="${base}zapas/${esc(g.game_id)}">
      <span class="rank num">${i + 1}</span>
      <span class="tipmain">${badge(t.team, sport, "sm", { value: ps[i], tone: "tip" })}<span class="abbr">${esc(t.team)}</span> <span class="muted">${where} ${esc(t.opp)}</span>
        <span class="tipmeta">${esc(shortDate(localDay(g.tipoff_utc, g.date)))} ${time(g.tipoff_utc)}${isPre(g) ? ` <span class="tag">príprava</span>` : ""}</span></span>
      <span class="tipp num">${ps[i]} %</span>
      ${i ? `<span class="acc">tipy 1 – ${i + 1} spolu: <b class="num">${acc[i]} %</b><span class="accbar" aria-hidden="true"><i style="width:${acc[i]}%"></i></span></span>` : `<span class="acc">najistejší tip</span>`}
    </a></li>`;
  });
  const top = list[0];
  const kpis = `<div class="kpis-row">
      <a class="card kpi-card" href="${base}zapas/${esc(top.game.game_id)}"><span class="label">Najistejší tip</span>
        <span class="kpi-team">${badge(top.team, sport, "sm", { value: ps[0], tone: "tip" })}<b>${esc(top.team)}</b><span class="kpi-n num tipp">${ps[0]} %</span></span></a>
      <div class="card kpi-card"><span class="label">Tipov</span><span class="kpi-n num">${list.length}</span><span class="kpi-l">zápasy, ktoré ešte nezačali</span></div>
      <div class="card kpi-card"><span class="label">Všetky naraz</span><span class="kpi-n num">${acc[acc.length - 1]} %</span><span class="kpi-l">súčin všetkých šancí</span></div>
    </div>`;
  return `${header("Tipy", `aktualizované ${esc(when(generatedAt))}`)}${intro}
    ${kpis}
    <div class="split">
      <div class="split-side">
        <p class="hint lead">Favoriti zápasov, ktoré ešte nezačali, od najväčšej šance podľa modelu. „Spolu“ je šanca, že vyjdú všetky tipy od prvého po daný riadok.</p>
        ${chart(acc, ps)}
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
