import type { AppData, Game, TeamState } from "../data";
import { chip, dayLabel, esc, header, pct, pulseNum, signed1, tierClass, tipoff, when } from "../ui";

function row(s: TeamState, where: string): string {
  return `<div class="row team-row">
      <span class="abbr">${esc(s.team)}</span><span class="where">${where}</span>${chip(s.tier)}
      <span class="num pulse-num ${tierClass(s.tier)}">${pulseNum(s.pulse)}</span>
    </div>`;
}

export function gameCard(g: Game): string {
  const levels = [g.home.confidence, g.away.confidence];
  const conf = levels.includes("nízka") ? "nízka" : levels.includes("stredná") ? "stredná" : "vysoká";
  const dropped = [g.home, g.away].find((s) => s.dropped);
  const flag = dropped
    ? `<span class="flag drop">▼ ${esc(dropped.team)} pod normálom</span>`
    : g.what_if.length
      ? `<span class="flag q">? ${esc(g.what_if[0].player)} otázny</span>`
      : "";
  return `<article class="card game" data-game="${esc(g.game_id)}">
    <a class="stretch" href="#/zapas/${esc(g.game_id)}" aria-label="Detail zápasu ${esc(g.away.team)} na palubovke ${esc(g.home.team)}"></a>
    <div class="row small"><span>${tipoff(g.tipoff_utc, g.date)}${g.neutral ? " · neutrálne ihrisko" : ""}${g.kind === "preseason" ? ` · <b class="pre">PRÍPRAVA</b>` : ""}</span><span>istota: <b>${conf}</b></span></div>
    ${row(g.home, g.neutral ? "" : "DOMA")}${row(g.away, g.neutral ? "" : "VONKU")}
    <div class="bar" role="img" aria-label="Šanca na výhru ${esc(g.home.team)} ${pct(g.p_home)}"><i style="width:${Math.round(g.p_home * 100)}%"></i></div>
    <div class="row small"><span>${esc(g.home.team)} <b>${pct(g.p_home)}</b></span><span>${flag}</span><span><b>${pct(1 - g.p_home)}</b> ${esc(g.away.team)}</span></div>
    <div class="row small"><span>očakávaný rozdiel ${signed1(g.margin_home)} ${esc(g.home.team)}</span></div>
  </article>`;
}

export function todayView(d: AppData): string {
  const p = d.predictions;
  const days = Object.entries(p.days).filter(([, games]) => games.length);
  const total = days.reduce((n, [, g]) => n + g.length, 0);
  const body = days.length
    ? days.map(([day, games]) => `<h2 class="section">// ${esc(dayLabel(day))} · ${games.length} ${games.length === 1 ? "zápas" : games.length < 5 ? "zápasy" : "zápasov"}</h2><div class="games">${games.map(gameCard).join("")}</div>`).join("")
    : `<p class="empty">Žiadne naplánované zápasy v najbližších dňoch.</p>`;
  return `${header("TEAM PULSE", "DNES", `${total} ${total === 1 ? "zápas" : total < 5 && total > 0 ? "zápasy" : "zápasov"}`)}
    ${body}
    <p class="meta">dni podľa amerického kalendára, časy začiatku v našom čase<br>aktualizované ${esc(when(p.generated_at))} · model ${esc(p.model)} · zranenia ${esc(p.injuries_matched ?? "")}</p>`;
}
