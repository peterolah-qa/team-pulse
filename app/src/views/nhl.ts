/* NHL (beta): zápasy, tipy, výsledky, liga podľa Ela a model. Tipy sa zamykajú raz ráno (Mac),
   appka ich len ukazuje. Zranenia z ESPN sú len informácia, model ich nepočíta (brána G2-NHL). */
import type { NhlData, NhlForm, NhlGame, NhlInjury, NhlOutcome, NhlResult, NhlSide, NhlStatKey } from "../data";
import { isFollowed } from "../follow";
import { badge, coin, dayHeading, dayTitle, esc, groupBy, header, localDay, num1, pct1, shortDate, signed, signed1, split, teamName, time, when } from "../ui";
import { byTipoff, gameRow, isPre, modelWidget } from "./games";
import { card, dayWidget, matchesPage, topReasons, type CardSide } from "./matches";
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

const STATUS: Record<NhlInjury["status"], [string, string]> = {
  OUT: ["nehrá", "t3"],
  SUSP: ["trest", "t3"],
  IR: ["dlhodobo", "t3"], // listina zranených (IR), aspoň 7 dní mimo
  DTD: ["otázny", "t1"],
  "?": ["neistý", "t1"],
};
const INJURY: Record<string, string> = {
  "Upper Body": "horná časť tela", "Lower Body": "dolná časť tela", Undisclosed: "neuvedené", Illness: "choroba",
  Concussion: "otras mozgu", Head: "hlava", Neck: "krk", Shoulder: "rameno", Elbow: "lakeť", Arm: "ruka", Wrist: "zápästie",
  Hand: "ruka", Finger: "prst", Back: "chrbát", Abdomen: "brucho", Ribs: "rebrá", Hip: "bedro", Groin: "slabiny", Leg: "noha",
  Thigh: "stehno", Hamstring: "zadný stehenný sval", Knee: "koleno", Ankle: "členok", Foot: "chodidlo", Achilles: "achilovka",
  Personal: "osobné dôvody",
};

/* Chýbajúci hráči jedného teamu (ESPN). Návrat je odhad ESPN, nie istota. */
function injuryRows(n: NhlData, team: string): string {
  const list = n.predictions.injuries?.[team] ?? [];
  if (!list.length) return `<li><span><b>${esc(team)}</b> <span class="muted">nikto nechýba</span></span></li>`;
  return list
    .map((p) => {
      const [label, tone] = STATUS[p.status] ?? STATUS["?"];
      const what = [p.pos, p.injury ? (INJURY[p.injury] ?? p.injury) : null].filter(Boolean).join(" · ");
      const [, m, d] = (p.return_date ?? "").split("-").map(Number);
      const back = d && p.status !== "DTD" ? `návrat asi ${d}. ${m}.` : "";
      return `<li><span><b>${esc(team)}</b> ${esc(p.player)} <span class="chip ${tone}">${label}</span>${what ? `<br><span class="small muted">${esc(what)}</span>` : ""}</span><span class="small muted nowrap">${back}</span></li>`;
    })
    .join("");
}

function injuriesCard(n: NhlData, g: NhlGame): string {
  if (n.predictions.injuries == null) return "";
  const stamp = n.predictions.injuries_timestamp ? ` (stav ${esc(when(n.predictions.injuries_timestamp))})` : "";
  return `<h2 class="sec">Chýbajúci hráči</h2><section class="card"><ul class="rows">${injuryRows(n, g.away.team)}${injuryRows(n, g.home.team)}</ul>
      <p class="small muted">Zranenia z ESPN${stamp}. Model NHL ich zatiaľ nepočíta, tip sa podľa nich nemení. Dlhodobo = listina zranených (IR).</p></section>`;
}

/* Poznámka pod zápasom: najväčší vplyv únavy na každý team („DET: back-to-back“). */
const fatigue = (g: NhlGame): string[] => [g.away, g.home].flatMap((s) => (s.reasons.length ? [`${s.team}: ${s.reasons[0][0]}`] : []));

/* NHL karta: prstenec = šanca na výhru v zápase (NHL nemá Pulse), dôvody = rozpad tipu v Elo bodoch. */
function nhlCard(g: NhlGame, i: number, cnt: number, now: number): string {
  const homeFav = g.p_home > 0.5;
  const { home, away } = split(g.p_home);
  const side = (s: "home" | "away"): CardSide => {
    const f = g.ctx?.[s]?.form;
    const isFav = (s === "home") === homeFav;
    return {
      ring: { value: s === "home" ? home : away, tone: isFav ? "tip" : "dim" },
      name: teamName(g[s].team, "nhl"),
      line: `${f ? `<span class="num">${f.record.join("-")}</span> · ` : ""}Elo <b class="num">${Math.round(g[s].elo)}</b>`,
    };
  };
  const sign = homeFav ? 1 : -1;
  const reasons: [string, number][] = g.ctx
    ? g.ctx.edge.items.filter(([k]) => k !== "base").map(([, label, v]) => [label, sign * v])
    : [g.away, g.home].flatMap((s) => s.reasons.map(([t, e]): [string, number] => [`${s.team}: ${t}`, (s === g.home) === homeFav ? e : -e]));
  return card(g, "nhl", { href: `${BASE}zapas/${esc(g.game_id)}`, away: side("away"), home: side("home"), reasons: topReasons(reasons), venue: g.ctx?.venue }, i, cnt, now);
}

function eloWidget(n: NhlData): string {
  const top = n.predictions.teams.slice(0, 5);
  if (!top.length) return "";
  return `<section class="card widget"><h2 class="label">Najsilnejší podľa Ela</h2><ol class="eloten">${top
    .map((t, i) => `<li><span class="num muted">${i + 1}.</span>${badge(t.team, "nhl")}<b>${esc(t.team)}</b><span class="muted">${esc(teamName(t.team, "nhl"))}</span><span class="num">${Math.round(t.elo)}</span></li>`)
    .join("")}</ol><a class="wlink" href="${BASE}teamy">Celá liga podľa Ela ›</a></section>`;
}

export function nhlGamesView(n: NhlData): string {
  const done = finished(n);
  const list = games(n).filter((g) => !done.has(g.game_id)).sort(byTipoff);
  const byId = new Map(list.map((g) => [g.game_id, g]));
  return matchesPage({
    sport: "nhl",
    games: list,
    sub: updated(n),
    intro: beta(),
    card: (g, i, cnt, now) => nhlCard(byId.get(g.game_id)!, i, cnt, now),
    row: (g, now) => gameRow(g, now, { sport: "nhl", notes: fatigue(byId.get(g.game_id)!) }),
    widgets: (day, gs) => `${dayWidget(day, gs, "nhl")}${eloWidget(n)}${modelWidget(n.model, `${BASE}model`)}`,
    footer: "Časy sú v našom čase. Tip = team, ktorému model dáva väčšiu šancu na výhru (aj po predĺžení alebo nájazdoch). Prstenec okolo teamu = šanca na výhru v zápase.",
    empty: "Žiadne zápasy s tipom. Tipy na ďalšie dni pribudnú ráno.",
  });
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

// --- detail zápasu ---------------------------------------------------------------------------------

const ICON = {
  share: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="19" r="2.5"/><path d="M8.2 10.8l7.6-4.4M8.2 13.2l7.6 4.4"/></svg>`,
  bell: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/></svg>`,
  check: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>`,
};

const LETTER: Record<NhlOutcome, string> = { W: "V", L: "P", OTL: "P" };
const OUTCOME: Record<NhlOutcome, string> = { W: "výhra", L: "prehra", OTL: "prehra po predĺžení alebo nájazdoch" };
const EXTRA_LONG: Record<string, string> = { OT: "po predĺžení", SO: "po nájazdoch" };

const plural = (n: number, w: [string, string, string]): string => (n === 1 ? w[0] : n >= 2 && n <= 4 ? w[1] : w[2]);
const dm = (iso: string): string => {
  const [y, m, d] = iso.split("-").map(Number);
  return `${d}. ${m}.${y !== new Date().getFullYear() ? ` ${y}` : ""}`;
};
const dayDiff = (a: string, b: string): number => Math.round((Date.parse(`${b}T12:00:00Z`) - Date.parse(`${a}T12:00:00Z`)) / 86_400_000);

/* „3-0-1“ + popis pre čítačky */
function record(r: [number, number, number]): string {
  const [w, l, o] = r;
  const spoken = `${w} ${plural(w, ["výhra", "výhry", "výhier"])}, ${l} ${plural(l, ["prehra", "prehry", "prehier"])}, ${o} po predĺžení alebo nájazdoch`;
  return `<span aria-hidden="true">${w}-${l}-${o}</span><span class="sr-only">${spoken}</span>`;
}

/* Posledných 5 zápasov ako štvorčeky, najnovší vpravo. */
function dots(form?: NhlForm): string {
  if (!form?.last.length) return "";
  const games = [...form.last].reverse();
  const spoken = games.map((x) => OUTCOME[x.res]).join(", ");
  return `<span class="dots" role="img" aria-label="Posledné zápasy od najstaršieho: ${spoken}">${games
    .map((x) => `<span class="dot5 ${x.res}" title="${esc(`${dm(x.date)} ${x.home ? "doma" : "vonku"} ${x.opp} ${x.gf}:${x.ga}`)}">${LETTER[x.res]}</span>`)
    .join("")}</span>`;
}

/* Fakty o odpočinku z rozpisu (rovnaké čísla ako vstupy modelu). Bez rozpisu dôvody únavy z tipu. */
function restFacts(g: NhlGame, side: "home" | "away"): string[] {
  const s = g[side];
  const r = g.ctx?.[side]?.rest;
  if (!r || r.rest === undefined) return s.reasons.map(([t]) => t);
  const out: string[] = [];
  if (r.b2b) out.push("back-to-back");
  else if (r.rest >= 7) out.push("6 a viac dní voľna");
  else out.push(`${r.rest - 1} ${plural(r.rest - 1, ["deň", "dni", "dní"])} voľna`);
  if (r.three_in4) out.push("3. zápas za 4 dni");
  if (r.tz_east) out.push(`posun o ${r.tz_east} h na východ`);
  if (r.road && r.road >= 2) out.push(`${r.road}. zápas výjazdu`);
  return out;
}

function hero(g: NhlGame): string {
  const { home, away } = split(g.p_home);
  const homeFav = g.p_home > 0.5;
  const fav = homeFav ? g.home.team : g.away.team;
  const { title } = dayTitle(localDay(g.tipoff_utc, g.date));
  const day = title === "Dnes" || title === "Zajtra" || title === "Včera" ? title : shortDate(localDay(g.tipoff_utc, g.date));
  const col = (side: "home" | "away") => {
    const s = g[side];
    const f = g.ctx?.[side]?.form;
    return `<div class="tcol${side === "home" ? " r" : ""}">
      ${coin(s.team, true, "nhl")}
      <span class="where">${side === "home" ? (g.neutral ? "neutrálne" : "domáci") : "hostia"}</span>
      <span class="tfull">${esc(teamName(s.team, "nhl"))}</span>
      ${f ? `<span class="rec">${record(f.record)}</span>${dots(f)}` : ""}
    </div>`;
  };
  const facts = (["away", "home"] as const)
    .map((side) => [g[side].team, restFacts(g, side)] as const)
    .filter(([, f]) => f.length)
    .map(([t, f]) => `<li><b>${esc(t)}</b><span>${f.map(esc).join(" · ")}</span></li>`)
    .join("");
  return `<section class="hero2" aria-labelledby="match-title">
    <div class="hmeta"><span class="when2">${esc(day)} ${time(g.tipoff_utc)}</span>${g.ctx?.venue ? `<span>${esc(g.ctx.venue)}</span>` : ""}${isPre(g) ? `<span class="tag">príprava</span>` : ""}</div>
    <div class="pair">${col("away")}${col("home")}</div>
    <div class="probs"><span class="pnum${homeFav ? "" : " fav"}">${away} %</span><span class="plbl">šanca na výhru</span><span class="pnum${homeFav ? " fav" : ""}">${home} %</span></div>
    <div class="bar ${homeFav ? "home-fav" : "away-fav"}" role="img" aria-label="Šanca na výhru: ${esc(g.away.team)} ${away} %, ${esc(g.home.team)} ${home} %"><i style="width:${away}%"></i></div>
    <p class="tipbox"><span class="tip">tip</span><span class="what">${esc(fav)} vyhrá</span><span class="small muted">aj po predĺžení alebo nájazdoch</span></p>
    ${facts ? `<ul class="facts" aria-label="Odpočinok a cestovanie">${facts}</ul>` : ""}
  </section>`;
}

function sure(n: NhlData, g: NhlGame): string {
  const p = Math.max(g.p_home, 1 - g.p_home);
  const level = p >= 0.65 ? "výrazný favorit" : p >= 0.57 ? "mierny favorit" : "vyrovnaný zápas";
  const acc = n.model.test_metrics.accuracy;
  const pos = ((p - 0.5) / 0.5) * 100;
  return `<h2 class="sec">Istota tipu</h2><section class="card sure">
    <span class="level">${level}</span>
    <div class="scale" role="img" aria-label="Šanca favorita ${Math.round(p * 100)} % na stupnici od 50 do 100 %"><i style="left:${pos.toFixed(1)}%"></i></div>
    <div class="ends" aria-hidden="true"><span>50 % vyrovnané</span><span>100 % istota</span></div>
    <p>Z 10 takýchto zápasov by favorit vyhral asi <b>${Math.round(p * 10)}</b>. Hokej je náhodný, aj silný favorit často prehrá.</p>
    <p class="small muted">V teste na sezónach ${esc(n.model.test_metrics.test_seasons)} tip vyšiel v ${pct1(acc)} zápasov.</p>
  </section>`;
}

/* Prečo má tip svoju šancu: Elo body z pohľadu tipovaného teamu, súčet = zamknutá šanca. */
function edgeCard(n: NhlData, g: NhlGame): string {
  const e = g.ctx?.edge;
  if (!e) return "";
  const homeFav = g.p_home > 0.5;
  const fav = homeFav ? g.home.team : g.away.team;
  const sign = homeFav ? 1 : -1;
  const p = Math.round((homeFav ? g.p_home : 1 - g.p_home) * 100);
  const big = e.items.filter(([, , v]) => Math.abs(v) >= 1);
  const small = e.items.filter(([, , v]) => Math.abs(v) < 1);
  const rows: [string, string, number][] = big.map(([k, label, v]) => [k, label, sign * v]);
  if (small.length) rows.push(["small", "Drobné vplyvy (spolu)", sign * small.reduce((a, [, , v]) => a + v, 0)]);
  const max = Math.max(20, ...rows.map(([, , v]) => Math.abs(v)));
  const elo = (s: NhlSide) => `${s.team} ${Math.round(s.elo)}`;
  const label = (k: string, text: string) =>
    k === "elo" ? `${esc(text)}<small>${esc(elo(g.away))} : ${esc(elo(g.home))}</small>` : k === "base" ? `${esc(text)}<small>platí pre každý zápas</small>` : esc(text);
  const body = rows
    .map(([k, text, v]) => {
      const w = (Math.abs(v) / max) * 50;
      const cls = v >= 0 ? "plus" : "minus";
      const pos = v >= 0 ? `left:50%;width:${w.toFixed(1)}%` : `right:50%;width:${w.toFixed(1)}%`;
      return `<div class="erow"><span class="lbl">${label(k, text)}</span><span class="ebar" aria-hidden="true"><i class="${cls}" style="${pos}"></i></span><span class="ev ${cls}">${signed1(v)}</span></div>`;
    })
    .join("");
  const note = e.verified
    ? `<p class="okchip">${ICON.check}Prepočítané: z rozpisu a Ela model znova dá presne zamknutú šancu.</p>`
    : `<p class="small muted">Rozpis klubov nie je k dispozícii, rozpad je zo zamknutého tipu. Konštanta modelu a vplyvy pod 10 bodov sú spolu v poslednom riadku.</p>`;
  return `<h2 class="sec">Prečo ${p} % pre ${esc(fav)}</h2><section class="card edge">
    ${body}
    <div class="etotal"><span>Spolu v prospech ${esc(fav)}</span><span class="num">${signed1(sign * e.total)} Elo → ${p} %</span></div>
    ${note}
    <p class="small muted">Elo body: kladné pomáhajú tipu, záporné mu uberajú. Váhy sú naučené z ${new Intl.NumberFormat("sk-SK").format(n.model.n_games)} zápasov NHL, niektoré idú proti intuícii (napr. deň voľna navyše domácim mierne uberá).</p>
  </section>`;
}

function eloSpark(points: [string, number][]): string {
  const w = 120, h = 32, pad = 4;
  const vals = points.map(([, e]) => e);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const span = Math.max(hi - lo, 20);
  const mid = (lo + hi) / 2;
  const x = (i: number) => pad + (i / (vals.length - 1)) * (w - 2 * pad);
  const y = (v: number) => h / 2 - ((v - mid) / span) * (h - 2 * pad);
  const pts = vals.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const last = vals.length - 1;
  return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true"><polyline points="${pts}"/><circle cx="${x(last).toFixed(1)}" cy="${y(vals[last]).toFixed(1)}" r="3"/></svg>`;
}

function trendCard(g: NhlGame): string {
  const t = g.ctx?.trend;
  if (!t) return "";
  const row = (s: NhlSide, pts: [string, number][]) => {
    if (pts.length < 2)
      return `<div class="trow"><span class="abbr">${esc(s.team)}</span><span class="small muted">zatiaľ 1 zápas s tipom</span><span class="tv">${Math.round(s.elo)}</span></div>`;
    const d = Math.round(pts[pts.length - 1][1] - pts[0][1]);
    return `<div class="trow" role="img" aria-label="Elo ${esc(s.team)} pred zápasmi od ${dm(pts[0][0])}: z ${Math.round(pts[0][1])} na ${Math.round(pts[pts.length - 1][1])}">
      <span class="abbr">${esc(s.team)}</span>${eloSpark(pts)}<span class="tv">${Math.round(pts[pts.length - 1][1])}<small class="${d > 0 ? "pos" : d < 0 ? "neg" : "muted"}">${signed(d)} od ${dm(pts[0][0])}</small></span></div>`;
  };
  return `<h2 class="sec">Elo trend</h2><section class="card trend2">
    ${row(g.away, t.away)}${row(g.home, t.home)}
    <p class="small muted">Elo pred každým zápasom s tipom (od 13. 10. 2026), posledný bod = pred týmto zápasom. Priemer ligy 1505.</p>
  </section>`;
}

function restCard(g: NhlGame): string {
  const card = (side: "home" | "away") => {
    const s = g[side];
    const r = g.ctx?.[side]?.rest;
    const facts = restFacts(g, side);
    let prev = "";
    if (r?.prev) {
      const days = dayDiff(r.prev.date, g.date);
      const when = days === 1 ? "včera" : days === 2 ? "predvčerom" : `pred ${days} dňami`;
      prev = `<p>Naposledy <b>${when}</b> ${r.prev.home ? "doma s" : "vonku u"} ${esc(r.prev.opp)}, ${OUTCOME[r.prev.res]}</p>`;
    } else if (r) prev = `<p>Prvý zápas sezóny</p>`;
    const warn = (f: string) => /back-to-back|3\. zápas|posun|výjazdu/.test(f);
    return `<div class="card tcard"><h3>${coin(s.team, false, "nhl")}${esc(s.team)}</h3>${prev}
      ${facts.length ? `<div class="pills">${facts.map((f) => `<span class="pill${warn(f) ? " warn" : " ok"}">${esc(f)}</span>`).join("")}</div>` : `<p>Bez únavy</p>`}</div>`;
  };
  return `<h2 class="sec">Odpočinok a cestovanie</h2><div class="two">${card("away")}${card("home")}</div>`;
}

function formCard(g: NhlGame): string {
  if (!g.ctx?.home || !g.ctx?.away) return "";
  const card = (side: "home" | "away") => {
    const s = g[side];
    const f = g.ctx![side]!.form;
    const gpg = f.gf_pg != null && f.ga_pg != null ? `<p>Góly na zápas <b>${num2(f.gf_pg)} : ${num2(f.ga_pg)}</b></p>` : "";
    const list = f.last
      .map((x) => `<li><span class="dot5 ${x.res}" aria-hidden="true">${LETTER[x.res]}</span><span>${x.home ? "doma" : "u"} ${esc(x.opp)} <span class="sr-only">${OUTCOME[x.res]}</span></span><span class="sc">${x.gf}:${x.ga}${x.last ? ` <small class="muted">${x.last === "OT" ? "pp" : "sn"}</small>` : ""}</span></li>`)
      .join("");
    return `<div class="card tcard"><h3>${coin(s.team, false, "nhl")}${esc(s.team)} <span class="small muted">${record(f.record)}</span></h3>
      <p>Doma <b>${record(f.home_record)}</b></p><p>Vonku <b>${record(f.road_record)}</b></p>${gpg}
      ${list ? `<ul class="last5" aria-label="Posledné zápasy ${esc(s.team)}, od najnovšieho">${list}</ul>` : `<p>Ešte nehrali</p>`}</div>`;
  };
  return `<h2 class="sec">Forma v sezóne</h2><div class="two">${card("away")}${card("home")}</div>
    <p class="hint">V-P-P = výhry, prehry v riadnom čase, prehry po predĺžení alebo nájazdoch (základná časť). pp = po predĺžení, sn = po nájazdoch.</p>`;
}

const nf2 = new Intl.NumberFormat("sk-SK", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const num2 = (x: number): string => nf2.format(x);

const STAT_ROWS: [NhlStatKey, string, boolean, (x: number) => string][] = [
  ["gf", "Góly na zápas", false, num2],
  ["ga", "Inkasované góly", true, num2],
  ["pp", "Presilovky", false, (x) => pct1(x)],
  ["pk", "Oslabenia", false, (x) => pct1(x)],
  ["sf", "Strely na bránu", false, (x) => num1(x)],
  ["sa", "Strely súpera", true, (x) => num1(x)],
];

function compareCard(g: NhlGame): string {
  const a = g.ctx?.away?.stats, h = g.ctx?.home?.stats;
  if (!a || !h) return "";
  const rows = STAT_ROWS.map(([k, label, lower, fmt]) => {
    const av = a[k], hv = h[k];
    const max = Math.max(av, hv) || 1;
    const aBetter = lower ? av < hv : av > hv, hBetter = lower ? hv < av : hv > av;
    return `<div class="crow"><div class="cline">
        <span class="a${aBetter ? " better" : ""}">${fmt(av)}<span class="rk" title="poradie v lige">${a.rank[k]}.</span></span>
        <span class="c">${label}</span>
        <span class="h${hBetter ? " better" : ""}"><span class="rk" title="poradie v lige">${h.rank[k]}.</span>${fmt(hv)}</span></div>
      <div class="cbars" aria-hidden="true"><span><i class="${aBetter ? "better" : ""}" style="width:${((av / max) * 100).toFixed(0)}%"></i></span><span><i class="${hBetter ? "better" : ""}" style="width:${((hv / max) * 100).toFixed(0)}%"></i></span></div></div>`;
  }).join("");
  return `<h2 class="sec">Porovnanie</h2><section class="card cmp">
    <div class="cmph"><span>${esc(g.away.team)}</span><span>${esc(g.home.team)}</span></div>${rows}
    <p class="small muted">Malé číslo = poradie v lige (1. = najlepší), základná časť po ${a.gp} a ${h.gp} zápasoch. Zlatá = lepší v dvojici. Zdroj: štatistiky NHL.</p>
  </section>`;
}

function h2hCard(g: NhlGame): string {
  const list = g.ctx?.h2h;
  if (!list) return "";
  if (!list.length) return `<h2 class="sec">Vzájomné zápasy</h2><p class="empty">V tejto ani minulej sezóne spolu nehrali.</p>`;
  const rows = list
    .map((x) => {
      const winner = x.gh > x.ga ? x.home : x.away;
      const extra = x.last ? ` ${EXTRA_LONG[x.last]}` : "";
      return `<li><span><span class="sc">${esc(x.away)} ${x.ga}:${x.gh} ${esc(x.home)}</span><small>${dm(x.date)} · doma ${esc(x.home)}${x.type === "P" ? " · playoff" : ""}${extra}</small></span><span class="wchip">výhra ${esc(winner)}</span></li>`;
    })
    .join("");
  return `<h2 class="sec">Vzájomné zápasy</h2><ul class="card h2h">${rows}</ul>
    <p class="hint">Posledné ${list.length === 1 ? "stretnutie" : `${list.length} stretnutia`} v tejto a minulej sezóne, skóre hostia : domáci.</p>`;
}

export function nhlGameView(n: NhlData, id: string): string {
  const back = { href: BASE, label: "Zápasy" };
  const g = games(n).find((x) => x.game_id === id);
  if (!g) return `${header("Zápas sa nenašiel", "", back)}<p class="empty">Tento zápas už nie je medzi tipmi. <a href="${BASE}">Späť na zápasy</a></p>`;
  const label = `${g.away.team} @ ${g.home.team}`;
  const on = isFollowed("nhl", g.game_id);
  const stamp = n.predictions.context_at ? ` Kontext z ${esc(when(n.predictions.context_at))}.` : "";
  return `<header class="top"><div class="dtop"><a class="back" href="${back.href}">‹ ${esc(back.label)}</a>
      <button type="button" class="iconbtn" id="share" aria-label="Zdieľať zápas">${ICON.share}</button></div>
    <h1 class="match-h" id="match-title">${esc(g.away.team)} <span class="at">@</span> ${esc(g.home.team)}</h1></header>
    ${hero(g)}
    ${beta()}
    ${sure(n, g)}
    ${edgeCard(n, g)}
    ${trendCard(g)}
    ${restCard(g)}
    ${formCard(g)}
    ${compareCard(g)}
    ${h2hCard(g)}
    ${injuriesCard(n, g)}
    <p class="meta">Tip zamknutý ${esc(when(g.locked_at))}, po začiatku zápasu sa už nemení. Forma, odpočinok, porovnanie a vzájomné zápasy sú len informácia, model NHL ich počas brány G2-NHL nemení.${stamp} Zdroj: API NHL, zranenia ESPN.</p>
    <div class="cta"><button type="button" class="follow" id="follow" aria-pressed="${on}" data-sport="nhl" data-id="${esc(g.game_id)}" data-label="${esc(label)}">${on ? ICON.check : ICON.bell}<span>${on ? "Sledujem zápas" : "Sledovať zápas"}</span></button></div>`;
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
    <p class="meta">Elo pred posledným zápasom s tipom, priemer ligy je 1505. Forma (Pulse) a súpisky zatiaľ len pri NBA, zranenia sú v detaile zápasu.</p>`;
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
