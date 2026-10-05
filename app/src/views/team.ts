import type { AppData, TeamPage } from "../data";
import { chip, dayLabel, esc, header, pulseNum, ring, signed, TEAM_NAMES } from "../ui";

function spark(t: TeamPage): string {
  const pts = t.trend;
  if (pts.length < 2) return `<p class="small muted">Trend sa zobrazí po prvých zápasoch.</p>`;
  const W = 340, H = 96, pad = 10;
  const ys = pts.map((p) => p.pulse);
  const lo = Math.min(...ys, 30) - 5, hi = Math.max(...ys, 70) + 5;
  const x = (i: number) => pad + (i * (W - 2 * pad)) / (pts.length - 1);
  const y = (v: number) => H - pad - ((v - lo) * (H - 2 * pad)) / (hi - lo);
  const line = pts.map((p, i) => `${x(i).toFixed(1)},${y(p.pulse).toFixed(1)}`).join(" ");
  const dots = pts
    .map((p, i) => `<circle cx="${x(i).toFixed(1)}" cy="${y(p.pulse).toFixed(1)}" r="3.5" class="${p.pts > p.opp_pts ? "win" : "loss"}"><title>${esc(p.date)} ${p.home ? "vs" : "@"} ${esc(p.opp)} ${p.pts}:${p.opp_pts}</title></circle>`)
    .join("");
  const g70 = y(70).toFixed(1);
  const last = pts[pts.length - 1];
  const wins = pts.filter((p) => p.pts > p.opp_pts).length;
  return `<svg class="spark" viewBox="0 0 ${W} ${H}" role="img" aria-label="Pulse v posledných ${pts.length} zápasoch, bilancia ${wins}–${pts.length - wins}, posledný ${pulseNum(last.pulse)}">
      <line x1="0" x2="${W}" y1="${g70}" y2="${g70}" class="guide"/><text x="${W - 4}" y="${Number(g70) - 4}" text-anchor="end" class="guide-lbl">SILNÝ</text>
      <polyline points="${line}" class="trend"/>${dots}</svg>
    <div class="row small muted"><span>bilancia ${wins}–${pts.length - wins}</span><span><span class="lg win">●</span> výhra <span class="lg">○</span> prehra</span></div>`;
}

const STATUS_CLASS: Record<string, string> = { HRÁ: "t0", QUESTIONABLE: "t1", DOUBTFUL: "t2", OUT: "t3", PROBABLE: "t0" };
const STATUS_TEXT: Record<string, string> = { HRÁ: "HRÁ", QUESTIONABLE: "OTÁZNY", DOUBTFUL: "SKÔR NIE", OUT: "OUT", PROBABLE: "SKÔR ÁNO" };

/* Dopad hráča: koľko Elo team stráca, keď chýba (OUT = −x), pri otáznom ±x, inak +x. */
function impact(status: string, elo: number): string {
  if (!elo) return `<span class="num w3 muted">0</span>`;
  if (status === "OUT") return `<span class="num w3 neg">−${elo}</span>`;
  if (status === "QUESTIONABLE" || status === "DOUBTFUL") return `<span class="num w3 q">±${elo}</span>`;
  return `<span class="num w3">+${elo}</span>`;
}

export function teamView(d: AppData, abbr: string): string {
  const t = d.teams.teams[abbr];
  if (!t) return `${header("TEAM", "NENÁJDENÝ")}<p class="empty">Team sa nenašiel. <a href="#/teamy">Všetky teamy</a></p>`;
  const roster = t.roster
    .map((r) => `<div class="reason"><span>${esc(r.player)} <span class="small muted">${Math.round(r.typical_min)} min</span></span>
      <span class="right"><span class="chip ${STATUS_CLASS[r.status] ?? "t1"}">${esc(STATUS_TEXT[r.status] ?? r.status)}</span>
      ${impact(r.status, r.impact_elo)}</span></div>`)
    .join("");
  const upcoming = t.upcoming.length
    ? t.upcoming.map((u) => `<a class="reason link" href="#/zapas/${esc(u.game_id)}"><span>${esc(dayLabel(u.date))}</span><span>${u.home ? "vs" : "@"} ${esc(u.opp)}${u.kind === "preseason" ? " · príprava" : ""}</span></a>`).join("")
    : `<p class="small muted">Žiadne naplánované zápasy.</p>`;
  const reasons = t.reasons.length
    ? t.reasons.map(([txt, e]) => `<div class="reason"><span>${esc(txt)}</span><span class="num ${e >= 0 ? "pos" : "neg"}">${signed(e)}</span></div>`).join("")
    : `<p class="small muted">Bez výrazných faktorov.</p>`;
  return `${header("TEAM", `${esc(TEAM_NAMES[abbr] ?? abbr)}`, `Elo ${Math.round(t.elo)}<br>#${t.rank} v lige`)}
    <section class="card duel single">${ring(t.pulse, t.tier, 120)}
      <div class="stack">${chip(t.tier)}${t.dropped ? `<div class="small note">normálne ${esc(t.normal_tier.toUpperCase())}</div>` : ""}
        <div class="small muted">stav dnes, bez únavy konkrétneho zápasu</div></div></section>
    <div class="cols"><div>
    <h2 class="section">// PREČO</h2><section class="card">${reasons}</section>
    <h2 class="section">// TREND · POSLEDNÝCH ${t.trend.length} ZÁPASOV</h2><section class="card">${spark(t)}</section>
    <h2 class="section">// NAJBLIŽŠIE ZÁPASY</h2><section class="card">${upcoming}</section>
    </div><div>
    <h2 class="section">// SÚPISKA · HODNOTA HRÁČA V ELO</h2><section class="card">${roster}</section>
    </div></div>`;
}

export function teamsView(d: AppData): string {
  const list = Object.values(d.teams.teams).sort((a, b) => a.rank - b.rank);
  return `${header("LIGA", "TEAMY", `${list.length} teamov`)}
    <section class="grid">${list
      .map((t) => `<a class="card tile" href="#/team/${esc(t.team)}" aria-label="${esc(TEAM_NAMES[t.team] ?? t.team)}, Pulse ${pulseNum(t.pulse)}, ${esc(t.tier)}">
        ${ring(t.pulse, t.tier, 54, false)}<div><div class="abbr">${esc(t.team)}</div>${chip(t.tier)}<div class="small muted">#${t.rank}</div></div></a>`)
      .join("")}</section>`;
}
