import type { AppData, Game, TeamState } from "../data";
import { allGames } from "../data";
import { chip, dayLabel, esc, header, pct, ring, signed, signed1, teamLink, TEAM_NAMES, tipoff } from "../ui";

const LAYERS: [keyof NonNullable<TeamState["layers"]> | "home_adv", string][] = [
  ["strength", "SILA (ELO)"],
  ["roster", "SÚPISKA"],
  ["players", "HRÁČI"],
  ["fatigue", "ÚNAVA"],
  ["home_adv", "PROSTREDIE"],
];

function half(v: number, side: "l" | "r"): string {
  const w = Math.min((Math.abs(v) / 80) * 100, 100); // 80 Elo ≈ plná polovica
  const cls = v >= 0 ? "pos" : "neg";
  return `<div class="half ${side}"><i class="${cls}" style="width:${w}%"></i></div>`;
}

function layerRows(g: Game): string {
  return LAYERS.map(([key, label]) => {
    const h = key === "home_adv" ? g.home_adv : (g.home.layers?.[key] ?? 0);
    const a = key === "home_adv" ? 0 : (g.away.layers?.[key] ?? 0);
    return `<div class="layer">
      <div class="lbl small">${label}</div>
      <div class="diverge"><span class="num v">${signed(Math.round(h))}</span>${half(h, "l")}<span class="axis"></span>${half(a, "r")}<span class="num v r">${signed(Math.round(a))}</span></div></div>`;
  }).join("");
}

function reasons(g: Game): string {
  const items = [g.home, g.away].flatMap((s) => s.reasons.map(([t, e]) => ({ team: s.team, t, e })));
  if (!items.length) return `<p class="small muted">Žiadne výrazné faktory – oba teamy v bežnom stave.</p>`;
  return items
    .map((r) => `<div class="reason"><span>${esc(r.team)}: ${esc(r.t)}</span><span class="num ${r.e >= 0 ? "pos" : "neg"}">${signed(r.e)}</span></div>`)
    .join("");
}

function side(s: TeamState): string {
  return `<div class="side">${ring(s.pulse, s.tier, 104)}<div>${chip(s.tier)}</div>
    <div class="small muted">istota ${esc(s.confidence ?? "")}</div></div>`;
}

export function gameView(d: AppData, id: string): string {
  const g = allGames(d.predictions).find((x) => x.game_id === id);
  if (!g) return `${header("ZÁPAS", "NENÁJDENÝ")}<p class="empty">Zápas sa nenašiel. <a href="#/">Späť na dnešné zápasy</a></p>`;
  const dropped = [g.home, g.away].filter((s) => s.dropped);
  return `${header(`${dayLabel(g.date)} · ZAČIATOK ${tipoff(g.tipoff_utc, g.date)}`, `${teamLink(g.home.team)} <span class="vs">vs</span> ${teamLink(g.away.team)}`, `${g.neutral ? "neutrálne ihrisko" : "doma"}<br>${esc(TEAM_NAMES[g.home.team] ?? g.home.team)}`)}
    <section class="card duel" aria-label="Porovnanie teamov">
      ${side(g.home)}
      <div class="center"><div class="big">${pct(g.p_home)}</div><div class="small muted">výhra ${esc(g.home.team)}</div>
        <div class="mid num">${signed1(g.margin_home)}</div><div class="small muted">očakávaný rozdiel</div></div>
      ${side(g.away)}
    </section>
    ${dropped.map((s) => `<p class="small note">${esc(s.team)} normálne: <b>${esc(s.normal_tier.toUpperCase())}</b> – dnes o úroveň nižšie</p>`).join("")}
    <div class="cols"><div>
    <h2 class="section">// VRSTVY MODELU (ELO) · ${esc(g.home.team)} ◂ ▸ ${esc(g.away.team)}</h2>
    <section class="card">${layerRows(g)}<p class="small muted legend">zelená = pomáha teamu, červená = oslabuje ho</p></section>
    </div><div>
    <h2 class="section">// PREČO</h2>
    <section class="card">${reasons(g)}</section>
    ${g.what_if.length ? `<a class="button" href="#/cokeby/${esc(g.game_id)}">Čo keby: ${esc(g.what_if[0].player)} (${esc(g.what_if[0].team)})</a>` : ""}
    </div></div>`;
}
