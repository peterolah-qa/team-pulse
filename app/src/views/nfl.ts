/* NFL (beta): zápasy, tipy, výsledky, tímy podľa Ela a model. Tipy zamyká GitHub Actions (nfl.yml) pred výkopom,
   appka ich len ukazuje. Dva modely: nfl-elo-v1 (hlavný tip, meria ho G2-NFL) a od týždňa 10 nfl-elo-qb-v1
   (+ náhradník quarterback). Zdroj výsledkov: nflverse games.csv (Lee Sharpe). */
import type { NflData, NflGame, NflLive, NflResult, NflSide } from "../data";
import { badge, coin, dayHeading, dayTitle, esc, groupBy, header, localDay, pct1, shortDate, signed, signed1, split, teamName, time, when } from "../ui";
import { byTipoff, gameRow, modelWidget } from "./games";
import { card, dayWidget, matchesPage, topReasons, type CardSide } from "./matches";
import { modelPage } from "./model";
import { tipsFrom, tipsPage } from "./tips";

const BASE = "#/nfl/";
const SOURCE = "Výsledky a quarterbacky: nflverse games.csv (Lee Sharpe).";

const games = (n: NflData): NflGame[] => Object.values(n.predictions.days).flat();
const finished = (n: NflData): Set<string> => new Set(n.predictions.results.map((r) => r.game_id));
const updated = (n: NflData): string =>
  `tipy z ${esc(when(n.predictions.last_locked ?? n.predictions.generated_at))} · výsledky ${esc(when(n.predictions.generated_at))}`;
const rec = (r: [number, number, number] | null): string => (r ? (r[2] ? r.join("-") : `${r[0]}-${r[1]}`) : "");

/* Ostré meranie modelu (G2): koľko tipov vyšlo a log loss oproti hranici stanovenej vopred. */
function liveLine(l: NflLive, label: string): string {
  const dates = `${shortDate(l.from)} – ${shortDate(l.to)}`;
  if (!l.n) return `${label}: ostré meranie ${dates}, zamknutých ${l.locked} tipov, zatiaľ bez výsledku.`;
  const ll = l.log_loss == null ? "" : `, log loss ${l.log_loss.toFixed(4).replace(".", ",")} (hranica ${l.limit.toFixed(4).replace(".", ",")})`;
  return `${label}: tip vyšiel v ${l.hits} z ${l.n} zápasov (${pct1(l.hits / l.n)})${ll}, meranie ${dates}.`;
}

function intro(n: NflData): string {
  const l = n.predictions.live.elo;
  const now = l.n ? `Zatiaľ tip vyšiel v ${l.hits} z ${l.n} zápasov (${pct1(l.hits / l.n)}).` : `Zamknutých ${l.locked} tipov, zatiaľ bez výsledku.`;
  return `<p class="hint beta-note"><span class="beta">beta</span><span>NFL je nová: model prešiel backtestom, ostré meranie beží do 10. 1. 2027. ${now}</span></p>`;
}

/* NFL karta: prstenec = šanca na výhru, dôvody = rozpad tipu v Elo bodoch. */
function nflCard(g: NflGame, i: number, cnt: number, now: number): string {
  const homeFav = g.p_home > 0.5;
  const { home, away } = split(g.p_home);
  const side = (s: "home" | "away"): CardSide => ({
    ring: { value: s === "home" ? home : away, tone: (s === "home") === homeFav ? "tip" : "dim" },
    name: teamName(g[s].team, "nfl"),
    line: `${g.record[s] ? `<span class="num">${rec(g.record[s])}</span> · ` : ""}Elo <b class="num">${Math.round(g[s].elo)}</b>`,
  });
  const sign = homeFav ? 1 : -1;
  const reasons = g.edge.items.map(([, label, v]): [string, number] => [label, sign * v]);
  return card(g, "nfl", { href: `${BASE}zapas/${esc(g.game_id)}`, away: side("away"), home: side("home"), reasons: topReasons(reasons) }, i, cnt, now);
}

function eloWidget(n: NflData): string {
  const top = n.predictions.teams.slice(0, 5);
  if (!top.length) return "";
  return `<section class="card widget"><h2 class="label">Najsilnejší podľa Ela</h2><ol class="eloten">${top
    .map((t, i) => `<li><span class="num muted">${i + 1}.</span>${badge(t.team, "nfl")}<b>${esc(t.team)}</b><span class="muted">${esc(teamName(t.team, "nfl"))}</span><span class="num">${Math.round(t.elo)}</span></li>`)
    .join("")}</ol><a class="wlink" href="${BASE}teamy">Celá liga podľa Ela ›</a></section>`;
}

/* Poznámka pod zápasom: quarterbacky (očakávaní štartéri v čase zamknutia). */
const qbNote = (g: NflGame): string[] => (g.away.qb && g.home.qb ? [`QB ${g.away.qb} – ${g.home.qb}`] : []);

export function nflGamesView(n: NflData): string {
  const done = finished(n);
  const list = games(n).filter((g) => !done.has(g.game_id)).sort(byTipoff);
  const byId = new Map(list.map((g) => [g.game_id, g]));
  return matchesPage({
    sport: "nfl",
    games: list,
    sub: updated(n),
    intro: intro(n),
    card: (g, i, cnt, now) => nflCard(byId.get(g.game_id)!, i, cnt, now),
    row: (g, now) => gameRow(g, now, { sport: "nfl", notes: qbNote(byId.get(g.game_id)!) }),
    widgets: (day, gs) => `${dayWidget(day, gs, "nfl")}${eloWidget(n)}${modelWidget(n.model, `${BASE}model`)}`,
    footer: "Časy sú v našom čase. Tip = tím, ktorému model dáva väčšiu šancu na výhru (aj po predĺžení). Tipy na ďalší týždeň pribudnú, keď sa dohrá aktuálny.",
    empty: "Žiadne zápasy s tipom. Tipy na ďalší týždeň pribudnú, keď sa dohrá aktuálny (zvyčajne v utorok).",
  });
}

export function nflTipsView(n: NflData): string {
  const list = tipsFrom(games(n), finished(n));
  if (!list.length) return `${header("Tipy")}${intro(n)}<p class="empty">Žiadne zápasy, ktoré ešte nezačali. Tipy na ďalší týždeň pribudnú, keď sa dohrá aktuálny.</p>`;
  return tipsPage(
    list,
    n.predictions.last_locked ?? n.predictions.generated_at,
    "nfl",
    "Percentá sú z modelu Elo (backtest 2023 – 2025: 63,9 % trafených víťazov), nie od stávkových kancelárií. Naostro ich overuje brána G2-NFL do 10. 1. 2027.",
    intro(n),
  );
}

function tipOf(r: NflResult): { fav: string; p: number; hit: boolean } | null {
  if (r.p_home == null || r.score_home === r.score_away) return null; // remíza sa nevyhodnocuje
  const { home, away } = split(r.p_home);
  const homeFav = r.p_home > 0.5;
  return { fav: homeFav ? r.home : r.away, p: homeFav ? home : away, hit: homeFav === r.score_home > r.score_away };
}

function resultRow(r: NflResult): string {
  const homeWon = r.score_home > r.score_away;
  const tie = r.score_home === r.score_away;
  const t = tipOf(r);
  const line = (team: string, pts: number, won: boolean, home: boolean) => `<div class="tl${won ? " won" : ""}">
      ${coin(team, false, "nfl")}<span class="abbr">${esc(team)}</span>${home ? `<span class="home">doma</span>` : ""}<span class="val">${pts}</span></div>`;
  const tipline = t
    ? `<p class="tipline">Tip ${esc(t.fav)} ${t.p} % · <b>${t.hit ? "vyšiel" : "nevyšiel"}</b></p>`
    : tie
      ? `<p class="tipline muted">Remíza, tip sa nevyhodnocuje</p>`
      : `<p class="tipline muted">Pred ostrým meraním, bez tipu</p>`;
  return `<li><div class="match result ${t ? (t.hit ? "hit" : "miss") : "none"}">
    <div class="when"><span class="clock">${r.tipoff_utc ? time(r.tipoff_utc) : ""}</span><span class="tag">${r.week}. týždeň</span></div>
    <div class="teams">${line(r.away, r.score_away, !homeWon && !tie, false)}${line(r.home, r.score_home, homeWon, true)}</div>
    ${tipline}
  </div></li>`;
}

export function nflResultsView(n: NflData): string {
  const results = [...n.predictions.results].reverse();
  if (!results.length) return `${header("Výsledky")}${intro(n)}<p class="empty">Za posledný týždeň sa nedohral žiadny zápas NFL.</p>`;
  const tips = results.map(tipOf).filter((t) => t !== null);
  const hits = tips.filter((t) => t.hit).length;
  const days = groupBy(results, (r) => (r.tipoff_utc ? localDay(r.tipoff_utc, r.date) : r.date));
  return `${header("Výsledky", tips.length ? `tipy vyšli v <b>${hits} z ${tips.length}</b> zápasov` : "")}${intro(n)}
    ${days.map(([day, rs]) => `<section>${dayHeading(day, rs.length, ["zápas", "zápasy", "zápasov"])}<ul class="list">${rs.map(resultRow).join("")}</ul></section>`).join("")}
    <p class="meta">Výsledky za posledných 8 dní, skóre hostia : domáci. Červený zápas = náš tip nevyšiel. ${SOURCE}</p>`;
}

export function nflTeamsView(n: NflData): string {
  const list = n.predictions.teams;
  if (!list.length) return `${header("Teamy")}<p class="empty">Zatiaľ žiadne tímy.</p>`;
  const elos = list.map((t) => t.elo);
  const lo = Math.min(...elos) - 20, hi = Math.max(...elos);
  const rows = list
    .map((t, i) => `<li><div class="teamrow">
      <span class="rank num">${i + 1}</span><span class="abbr">${coin(t.team, false, "nfl")}${esc(t.team)}</span><span class="name">${esc(teamName(t.team, "nfl"))} <span class="muted num">${rec(t.record)}</span></span>
      <span class="meter elo" aria-hidden="true"><i style="width:${(((t.elo - lo) / (hi - lo)) * 100).toFixed(0)}%"></i></span>
      <span class="pulse num elo">${Math.round(t.elo)}</span></div></li>`)
    .join("");
  return `${header("Teamy", "sila podľa výsledkov (Elo), od najsilnejšieho")}
    <section><h2 class="day"><span>Liga podľa Ela</span><span class="day-n">${list.length}</span></h2><ul class="list tight">${rows}</ul></section>
    <p class="meta">Elo po poslednom odohranom zápase, priemer ligy 1505, bilancia v sezóne (výhry-prehry). ${SOURCE}</p>`;
}

const NFL_WEIGHTS: Record<string, string> = {
  home: "Domáce ihrisko",
  qb_backup: "Náhradník quarterback (druhý model)",
};

export function nflModelView(n: NflData): string {
  const live = `<section class="card"><h2 class="label">Ostré meranie (G2)</h2><ul class="rows">
      <li><span>${esc(liveLine(n.predictions.live.elo, "Elo"))}</span></li>
      <li><span>${esc(liveLine(n.predictions.live.qb, "Elo + quarterback"))}</span></li></ul></section>`;
  return modelPage(
    n.model,
    NFL_WEIGHTS,
    "Model Elo podľa FiveThirtyEight: sila tímu z výsledkov, výhoda domáceho ihriska, v play-off väčší rozdiel. Druhý model navyše uberie tímu 65 Elo, keď nastúpi náhradník namiesto bežného quarterbacka.",
    live,
  );
}

// --- detail zápasu ---------------------------------------------------------------------------------

const dm = (iso: string): string => {
  const [y, m, d] = iso.split("-").map(Number);
  return `${d}. ${m}.${y !== new Date().getFullYear() ? ` ${y}` : ""}`;
};

function hero(g: NflGame): string {
  const { home, away } = split(g.p_home);
  const homeFav = g.p_home > 0.5;
  const fav = homeFav ? g.home.team : g.away.team;
  const { title } = dayTitle(localDay(g.tipoff_utc, g.date));
  const day = title === "Dnes" || title === "Zajtra" || title === "Včera" ? title : shortDate(localDay(g.tipoff_utc, g.date));
  const col = (side: "home" | "away") => {
    const s = g[side];
    return `<div class="tcol${side === "home" ? " r" : ""}">
      ${coin(s.team, true, "nfl")}
      <span class="where">${side === "home" ? (g.neutral ? "neutrálne" : "domáci") : "hostia"}</span>
      <span class="tfull">${esc(teamName(s.team, "nfl"))}</span>
      ${g.record[side] ? `<span class="rec">${rec(g.record[side])}</span>` : ""}
    </div>`;
  };
  return `<section class="hero2" aria-labelledby="match-title">
    <div class="hmeta"><span class="when2">${esc(day)} ${time(g.tipoff_utc)}</span><span>${g.week}. týždeň</span>${g.kind === "playoff" ? `<span class="tag">play-off</span>` : ""}</div>
    <div class="pair">${col("away")}${col("home")}</div>
    <div class="probs"><span class="pnum${homeFav ? "" : " fav"}">${away} %</span><span class="plbl">šanca na výhru</span><span class="pnum${homeFav ? " fav" : ""}">${home} %</span></div>
    <div class="bar ${homeFav ? "home-fav" : "away-fav"}" role="img" aria-label="Šanca na výhru: ${esc(g.away.team)} ${away} %, ${esc(g.home.team)} ${home} %"><i style="width:${away}%"></i></div>
    <p class="tipbox"><span class="tip">tip</span><span class="what">${esc(fav)} vyhrá</span><span class="small muted">aj po predĺžení</span></p>
  </section>`;
}

function sure(n: NflData, g: NflGame): string {
  const p = Math.max(g.p_home, 1 - g.p_home);
  const level = p >= 0.7 ? "výrazný favorit" : p >= 0.58 ? "mierny favorit" : "vyrovnaný zápas";
  const pos = ((p - 0.5) / 0.5) * 100;
  return `<h2 class="sec">Istota tipu</h2><section class="card sure">
    <span class="level">${level}</span>
    <div class="scale" role="img" aria-label="Šanca favorita ${Math.round(p * 100)} % na stupnici od 50 do 100 %"><i style="left:${pos.toFixed(1)}%"></i></div>
    <div class="ends" aria-hidden="true"><span>50 % vyrovnané</span><span>100 % istota</span></div>
    <p>Z 10 takýchto zápasov by favorit vyhral asi <b>${Math.round(p * 10)}</b>.</p>
    <p class="small muted">V teste na sezónach ${esc(n.model.test_metrics.test_seasons)} tip vyšiel v ${pct1(n.model.test_metrics.accuracy)} zápasov.</p>
  </section>`;
}

const CHECK = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>`;

function edgeCard(g: NflGame): string {
  const e = g.edge;
  const homeFav = g.p_home > 0.5;
  const fav = homeFav ? g.home.team : g.away.team;
  const sign = homeFav ? 1 : -1;
  const p = Math.round((homeFav ? g.p_home : 1 - g.p_home) * 100);
  const max = Math.max(20, ...e.items.map(([, , v]) => Math.abs(v)));
  const elo = (s: NflSide) => `${s.team} ${Math.round(s.elo)}`;
  const body = e.items
    .map(([k, text, raw]) => {
      const v = sign * raw;
      const w = (Math.abs(v) / max) * 50;
      const cls = v >= 0 ? "plus" : "minus";
      const pos = v >= 0 ? `left:50%;width:${w.toFixed(1)}%` : `right:50%;width:${w.toFixed(1)}%`;
      const label = k === "elo" ? `${esc(text)}<small>${esc(elo(g.away))} : ${esc(elo(g.home))}</small>` : esc(text);
      return `<div class="erow"><span class="lbl">${label}</span><span class="ebar" aria-hidden="true"><i class="${cls}" style="${pos}"></i></span><span class="ev ${cls}">${signed1(v)}</span></div>`;
    })
    .join("");
  const note = e.verified
    ? `<p class="okchip">${CHECK}Prepočítané: z výsledkov v games.csv model znova dá presne zamknutú šancu.</p>`
    : `<p class="small muted">Rozpad je zo zamknutého tipu; prepočet z aktuálnych dát sa líši (napr. opravený výsledok).</p>`;
  return `<h2 class="sec">Prečo ${p} % pre ${esc(fav)}</h2><section class="card edge">
    ${body}
    <div class="etotal"><span>Spolu v prospech ${esc(fav)}</span><span class="num">${signed1(sign * e.total)} Elo → ${p} %</span></div>
    ${note}
  </section>`;
}

function qbCard(g: NflGame): string {
  if (!g.away.qb && !g.home.qb) return "";
  const row = (s: NflSide) => {
    const backup = s.reasons.length ? ` <span class="chip t2">náhradník ${signed(Math.round(s.reasons[0][1]))} Elo</span>` : "";
    return `<li><span><b>${esc(s.team)}</b> ${esc(s.qb ?? "neznámy")}${backup}</span></li>`;
  };
  const second = g.p_home_qb != null
    ? (() => {
        const hf = g.p_home_qb > 0.5;
        const p = Math.round((hf ? g.p_home_qb : 1 - g.p_home_qb) * 100);
        return `<p>Druhý model (Elo + quarterback): <b>${esc(hf ? g.home.team : g.away.team)} ${p} %</b></p>`;
      })()
    : `<p class="small muted">Druhý model s quarterbackom tipuje od 10. týždňa (12. 11.).</p>`;
  return `<h2 class="sec">Quarterbacky</h2><section class="card"><ul class="rows">${row(g.away)}${row(g.home)}</ul>${second}
    <p class="small muted">Očakávaní štartéri v čase zamknutia tipu. Ak sa quarterback zmení neskôr, tip sa nemení.</p></section>`;
}

function spark(points: [string, number][]): string {
  const w = 120, h = 32, pad = 4;
  const vals = points.map(([, e]) => e);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const span = Math.max(hi - lo, 20), mid = (lo + hi) / 2;
  const x = (i: number) => pad + (i / (vals.length - 1)) * (w - 2 * pad);
  const y = (v: number) => h / 2 - ((v - mid) / span) * (h - 2 * pad);
  const last = vals.length - 1;
  return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true"><polyline points="${vals.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ")}"/><circle cx="${x(last).toFixed(1)}" cy="${y(vals[last]).toFixed(1)}" r="3"/></svg>`;
}

function trendCard(g: NflGame): string {
  const row = (s: NflSide, pts: [string, number][]) => {
    if (pts.length < 2) return "";
    const d = Math.round(pts[pts.length - 1][1] - pts[0][1]);
    return `<div class="trow" role="img" aria-label="Elo ${esc(s.team)} pred zápasmi od ${dm(pts[0][0])}: z ${Math.round(pts[0][1])} na ${Math.round(pts[pts.length - 1][1])}">
      <span class="abbr">${esc(s.team)}</span>${spark(pts)}<span class="tv">${Math.round(pts[pts.length - 1][1])}<small class="${d > 0 ? "pos" : d < 0 ? "neg" : "muted"}">${signed(d)} od ${dm(pts[0][0])}</small></span></div>`;
  };
  const rows = row(g.away, g.trend.away) + row(g.home, g.trend.home);
  if (!rows) return "";
  return `<h2 class="sec">Elo trend</h2><section class="card trend2">${rows}
    <p class="small muted">Elo pred posledných 10 zápasov tímu vrátane tohto (aj z minulej sezóny), posledný bod = pred týmto zápasom. Priemer ligy 1505.</p></section>`;
}

export function nflGameView(n: NflData, id: string): string {
  const back = { href: BASE, label: "Zápasy" };
  const g = games(n).find((x) => x.game_id === id);
  if (!g) return `${header("Zápas sa nenašiel", "", back)}<p class="empty">Tento zápas už nie je medzi tipmi. <a href="${BASE}">Späť na zápasy</a></p>`;
  return `<header class="top"><div class="dtop"><a class="back" href="${back.href}">‹ ${esc(back.label)}</a>
      <button type="button" class="iconbtn" id="share" aria-label="Zdieľať zápas"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="19" r="2.5"/><path d="M8.2 10.8l7.6-4.4M8.2 13.2l7.6 4.4"/></svg></button></div>
    <h1 class="match-h" id="match-title">${esc(g.away.team)} <span class="at">@</span> ${esc(g.home.team)}</h1></header>
    ${hero(g)}
    ${sure(n, g)}
    ${edgeCard(g)}
    ${qbCard(g)}
    ${trendCard(g)}
    <p class="meta">Tip zamknutý ${esc(when(g.locked_at))}, po výkope sa už nemení. ${SOURCE}</p>`;
}
