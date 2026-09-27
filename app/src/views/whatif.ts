import type { AppData, Game, WhatIf } from "../data";
import { allGames } from "../data";
import { chip, dayLabel, esc, header, pct, ring } from "../ui";

function scenarioCard(g: Game, w: WhatIf, idx: number): string {
  const s = w.plays;
  const border = w.plays.tier !== w.out.tier;
  return `<section class="card whatif" data-idx="${idx}" aria-label="Scenár ${esc(w.player)}">
    <div class="row"><div><div class="player">${esc(w.player)} <span class="small muted">${esc(w.team)}</span></div>
      <div class="small muted">${esc(dayLabel(g.date))} · ${esc(g.away.team)} @ ${esc(g.home.team)} · šanca, že nenastúpi ${pct(w.p_out)} · dopad ${w.impact_elo} Elo</div></div></div>
    <div class="toggle-row" role="group" aria-label="Nastúpi ${esc(w.player)}?">
      <button type="button" class="toggle" data-choice="plays" aria-pressed="true">HRÁ</button>
      <button type="button" class="toggle" data-choice="out" aria-pressed="false">NEHRÁ</button>
    </div>
    <div class="row scenario">
      <div class="res" aria-live="polite">${ring(s.pulse, s.tier, 92)}</div>
      <div class="stack"><span class="small muted">stav ${esc(w.team)}</span><span class="tierbox">${chip(s.tier)}</span>
        <div class="small">výhra ${esc(g.home.team)}: <b class="num phome">${pct(s.p_home)}</b></div></div>
    </div>
    ${border ? `<p class="warn">⚠ HRANIČNÝ PRÍPAD – stav hráča preklopí úroveň teamu</p>` : ""}
    <script type="application/json" class="data">${JSON.stringify({ plays: w.plays, out: w.out, home: g.home.team }).replace(/</g, "\\u003c")}</script>
  </section>`;
}

export function whatIfView(d: AppData, gameId?: string): string {
  const games = allGames(d.predictions).filter((g) => !gameId || g.game_id === gameId);
  const cards = games.flatMap((g) => g.what_if.map((w) => ({ g, w })));
  const body = cards.length
    ? `<div class="games">${cards.map(({ g, w }, i) => scenarioCard(g, w, i)).join("")}</div>`
    : `<p class="empty">Žiadni otázni hráči v najbližších zápasoch. Keď Injury Report označí kľúčového hráča ako otázneho, tu uvidíš, čo to znamená.</p>`;
  return `${header("ČO KEBY", "OTÁZNI HRÁČI", `${cards.length} ${cards.length === 1 ? "scenár" : cards.length < 5 && cards.length > 0 ? "scenáre" : "scenárov"}`)}${body}`;
}

/* Prepínač HRÁ / NEHRÁ – prepne zobrazený scenár bez načítania stránky. */
export function bindWhatIf(root: HTMLElement): void {
  root.querySelectorAll<HTMLElement>(".whatif").forEach((card) => {
    const data = JSON.parse(card.querySelector(".data")!.textContent!);
    card.querySelectorAll<HTMLButtonElement>(".toggle").forEach((btn) => {
      btn.addEventListener("click", () => {
        const choice = btn.dataset.choice as "plays" | "out";
        const s = data[choice];
        card.querySelectorAll<HTMLButtonElement>(".toggle").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
        card.querySelector(".res")!.innerHTML = ring(s.pulse, s.tier, 92);
        card.querySelector(".tierbox")!.innerHTML = chip(s.tier);
        card.querySelector(".phome")!.textContent = pct(s.p_home);
      });
    });
  });
}
