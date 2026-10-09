/* Team: forma dnes, najbližšie zápasy s naším tipom, posledné výsledky, súpiska. Teamy: liga podľa formy. */
import type { AppData, Result, TeamPage, Tier } from "../data";
import { allGames } from "../data";
import { chip, coin, esc, header, localDay, parseUtc, pulseNum, ring, shortDate, signed, split, TEAM_NAMES, TIERS, tierClass, time } from "../ui";

const STATUS: Record<string, [string, string]> = {
  OUT: ["nehrá", "t3"],
  DOUBTFUL: ["skôr nie", "t2"],
  QUESTIONABLE: ["otázny", "t1"],
  PROBABLE: ["skôr áno", "t0"],
};
const SHOWN = 8;

/* Poradie podľa Pulse (rovnaké číslo ako na obrazovke, takže poradie vždy sedí). */
export function ranked(d: AppData): TeamPage[] {
  return Object.values(d.teams.teams).sort((a, b) => b.pulse - a.pulse || a.team.localeCompare(b.team));
}

function upcoming(d: AppData, t: TeamPage): string {
  if (!t.upcoming.length) return `<p class="muted">Žiadne naplánované zápasy.</p>`;
  const preds = new Map(allGames(d.predictions).map((g) => [g.game_id, g]));
  return `<ul class="rows">${t.upcoming
    .map((u) => {
      const g = preds.get(u.game_id);
      const tip = g ? split(g.p_home) : null;
      const mine = tip ? (u.home ? tip.home : tip.away) : null;
      const favMine = g ? (g.p_home > 0.5) === u.home : false;
      const day = shortDate(localDay(u.tipoff_utc ?? g?.tipoff_utc, u.date));
      const inner = `<span><span class="muted">${esc(day)} ${time(u.tipoff_utc ?? g?.tipoff_utc)}</span> ${g?.neutral ? "proti" : u.home ? "doma s" : "@"} <b>${esc(u.opp)}</b>${u.kind === "preseason" ? ` <span class="tag">príprava</span>` : ""}</span>
        <span class="nowrap">${mine === null ? `<span class="muted">tip zatiaľ nie je</span>` : `šanca <b class="num${favMine ? " pos" : ""}">${mine} %</b>`}</span>`;
      return g ? `<li><a href="#/zapas/${esc(u.game_id)}">${inner}<span class="chev" aria-hidden="true">›</span></a></li>` : `<li>${inner}</li>`;
    })
    .join("")}</ul>`;
}

function recent(d: AppData, t: TeamPage): string {
  const mine = (d.predictions.results ?? [])
    .filter((r) => r.home === t.team || r.away === t.team)
    .sort((a, b) => (parseUtc(b.tipoff_utc)?.getTime() ?? 0) - (parseUtc(a.tipoff_utc)?.getTime() ?? 0));
  const row = (r: Result) => {
    const home = r.home === t.team;
    const us = home ? r.pts_home : r.pts_away, them = home ? r.pts_away : r.pts_home;
    return `<li><a href="#/vysledok/${esc(r.game_id)}"><span><span class="wl ${us > them ? "w" : "l"}">${us > them ? "V" : "P"}</span>
      <span class="muted">${esc(shortDate(localDay(r.tipoff_utc, r.date)))}</span> ${home ? "doma s" : "@"} <b>${esc(home ? r.away : r.home)}</b>${r.kind === "preseason" ? ` <span class="tag">príprava</span>` : ""}</span>
      <b class="num">${us} : ${them}</b><span class="chev" aria-hidden="true">›</span></a></li>`;
  };
  const older = t.trend.slice(-5).reverse();
  const old = older
    .map((p) => `<li><span><span class="wl ${p.pts > p.opp_pts ? "w" : "l"}">${p.pts > p.opp_pts ? "V" : "P"}</span>
      <span class="muted">${esc(shortDate(p.date))}</span> ${p.home ? "doma s" : "@"} <b>${esc(p.opp)}</b></span><b class="num">${p.pts} : ${p.opp_pts}</b></li>`)
    .join("");
  const season = mine.length ? `<ul class="rows">${mine.map(row).join("")}</ul>` : "";
  const last = older.length && mine.length < 5 ? `<p class="small muted sub-h">${mine.length ? "Predtým, " : ""}koniec minulej sezóny</p><ul class="rows">${old}</ul>` : "";
  return season || last ? season + last : `<p class="muted">Zatiaľ žiadne odohrané zápasy.</p>`;
}

function roster(t: TeamPage): string {
  const order = (s: string) => (s in STATUS ? ["OUT", "DOUBTFUL", "QUESTIONABLE", "PROBABLE"].indexOf(s) : 9);
  const list = [...t.roster].sort((a, b) => order(a.status) - order(b.status) || b.impact_elo - a.impact_elo || b.typical_min - a.typical_min);
  const row = (r: (typeof list)[number]) => {
    const st = STATUS[r.status];
    return `<tr><td class="p">${esc(r.player)}${st ? ` <span class="chip ${st[1]}">${st[0]}</span>` : ""}</td>
      <td class="n">${Math.round(r.typical_min)}</td><td class="n">${r.impact_elo ? signed(r.impact_elo) : "–"}</td></tr>`;
  };
  const shown = Math.max(SHOWN, list.filter((r) => r.status in STATUS).length);
  const head = `<thead><tr><th scope="col">Hráč</th><th class="n" scope="col"><abbr title="očakávané minúty v zápase">MIN</abbr></th><th class="n wide" scope="col"><abbr title="o koľko Elo bodov team oslabí, keď hráč chýba">hodnota</abbr></th></tr></thead>`;
  const rest = list.slice(shown);
  return `<section class="card flush"><table class="table box"><caption class="sr-only">Súpiska ${esc(t.team)}</caption>${head}<tbody>${list.slice(0, shown).map(row).join("")}</tbody></table>
    ${rest.length ? `<details class="more inner"><summary>Ďalší hráči (${rest.length})</summary><table class="table box"><caption class="sr-only">Ďalší hráči ${esc(t.team)}</caption>${head.replace("<thead>", '<thead class="sr-only">')}<tbody>${rest.map(row).join("")}</tbody></table></details>` : ""}
    </section><p class="meta">Hodnota = o koľko Elo bodov team oslabí, keď hráč chýba. Nováčikovia a hráči bez minút majú hodnotu až po pár zápasoch.</p>`;
}

export function teamView(d: AppData, abbr: string): string {
  const t = d.teams.teams[abbr];
  const back = { href: "#/teamy", label: "Teamy" };
  if (!t) return `${header("Team sa nenašiel", "", back)}<p class="empty">Taký team nepoznáme. <a href="#/teamy">Všetky teamy</a></p>`;
  const rank = ranked(d).findIndex((x) => x.team === abbr) + 1;
  const reasons = t.reasons.length
    ? `<ul class="rows">${t.reasons.map(([txt, e]) => `<li><span>${esc(txt)}</span><span class="${e >= 0 ? "pos" : "neg"}">${e >= 0 ? "pomáha" : "oslabuje"} <span class="num">${signed(e)}</span></span></li>`).join("")}</ul>`
    : `<p class="muted">Žiadny výrazný faktor: zdraví hráči, bez únavy.</p>`;
  return `${header(`${coin(abbr)} ${esc(TEAM_NAMES[abbr] ?? abbr)}`, "", back)}
    <section class="card hero teamhero">${ring(t.pulse, t.tier)}
      <div><p class="big-l">Pulse ${pulseNum(t.pulse)} ${chip(t.tier)}</p>
      <p class="muted">${rank}. v lige podľa formy${t.dropped ? ` · normálne ${esc(t.normal_tier)}` : ""}</p></div></section>
    <p class="hint">Forma dnes, bez únavy z konkrétneho zápasu. Pri zápase sa k nej pripočíta únava a cestovanie, preto sa tam Pulse môže o pár bodov líšiť.</p>
    <h2 class="sec">Prečo</h2><section class="card">${reasons}</section>
    <h2 class="sec">Najbližšie zápasy</h2><section class="card">${upcoming(d, t)}</section>
    <h2 class="sec">Posledné zápasy</h2><section class="card">${recent(d, t)}</section>
    <h2 class="sec">Súpiska</h2>${roster(t)}`;
}

const GROUP: Record<Tier, string> = { Silný: "Silní", Stabilný: "Stabilní", Oslabený: "Oslabení", Kritický: "Kritickí" };

export function teamsView(d: AppData): string {
  const list = ranked(d);
  const groups = TIERS.map((tier) => [tier, list.filter((t) => t.tier === tier)] as const).filter(([, ts]) => ts.length);
  return `${header("Teamy", "forma dnes, od najlepšieho")}
    ${groups
      .map(([tier, ts]) => `<section><h2 class="day"><span>${GROUP[tier]}</span><span class="day-n">${ts.length}</span></h2><ul class="list tight">${ts
        .map((t) => `<li><a class="teamrow" href="#/team/${esc(t.team)}">
          <span class="rank num">${list.indexOf(t) + 1}</span><span class="abbr">${coin(t.team)}${esc(t.team)}</span><span class="name">${esc(TEAM_NAMES[t.team] ?? t.team)}</span>
          <span class="meter ${tierClass(t.tier)}" aria-hidden="true"><i style="width:${Math.max(0, Math.min(100, t.pulse))}%"></i></span>
          <span class="pulse num ${tierClass(t.tier)}">${pulseNum(t.pulse)}</span></a></li>`)
        .join("")}</ul></section>`)
      .join("")}
    <p class="meta">Pulse 0 – 100 je forma teamu dnes: sila z výsledkov, súpiska a chýbajúci hráči. Silný 70+, Stabilný 50 – 69, Oslabený 30 – 49, Kritický pod 30.</p>`;
}
