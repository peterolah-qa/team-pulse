/* Vstupný bod: načíta dáta, jednoduchý router (#/…), prepínanie obrazoviek. */
// Len latinka + latin-ext (slovenské znaky), nie thai/devanagari – menší download.
import "@fontsource/chakra-petch/latin-700.css";
import "@fontsource/chakra-petch/latin-ext-700.css";
import "@fontsource/barlow/latin-400.css";
import "@fontsource/barlow/latin-ext-400.css";
import "@fontsource/barlow/latin-600.css";
import "@fontsource/barlow/latin-ext-600.css";
import "./style.css";

import { loadData, type AppData } from "./data";
import { markViewed, showToasts, takeNew, updateBadge } from "./notify";
import { gameView } from "./views/game";
import { gamesView } from "./views/games";
import { modelView } from "./views/model";
import { resultsView, resultView } from "./views/result";
import { teamsView, teamView } from "./views/team";
import { tipsView } from "./views/tips";

const app = document.getElementById("app")!;
let data: AppData | null = null;

function route(): { tab: string; html: string; title: string } {
  const [, page = "", arg = ""] = (location.hash || "#/").split("/");
  const d = data!;
  const id = decodeURIComponent(arg);
  switch (page) {
    case "zapas":
      return { tab: "zapasy", html: gameView(d, id), title: "Zápas" };
    case "cokeby": // staré odkazy na „Čo keby“ vedú na detail zápasu
      return arg ? { tab: "zapasy", html: gameView(d, id), title: "Zápas" } : { tab: "zapasy", html: gamesView(d), title: "Zápasy" };
    case "tipy":
      return { tab: "tipy", html: tipsView(d), title: "Tipy" };
    case "vysledky":
      return { tab: "vysledky", html: resultsView(d), title: "Výsledky" };
    case "vysledok":
      return { tab: "vysledky", html: resultView(d, id), title: "Výsledok" };
    case "teamy":
      return { tab: "teamy", html: teamsView(d), title: "Teamy" };
    case "team":
      return { tab: "teamy", html: teamView(d, id), title: id };
    case "model":
      return { tab: "model", html: modelView(d), title: "Model" };
    default:
      return { tab: "zapasy", html: gamesView(d), title: "Zápasy" };
  }
}

function render(): void {
  if (!data) return;
  const r = route();
  app.innerHTML = r.html;
  document.title = `${r.title} · Team Pulse`;
  document.querySelectorAll<HTMLAnchorElement>(".tabbar a").forEach((a) => {
    if (a.dataset.tab === r.tab) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  if (r.tab === "vysledky") markViewed(data);
  updateBadge(data);
  window.scrollTo(0, 0);
}

/* Nové dáta: upozornenia na dohrané zápasy a číslo na záložke Výsledky. */
function announce(): void {
  if (!data) return;
  showToasts(takeNew(data));
  updateBadge(data);
}

/* Po návrate appky z pozadia stiahne čerstvé dáta (zobrazí sa pri ďalšom kliknutí) a ukáže, čo skončilo. */
async function refresh(): Promise<void> {
  if (!data || document.visibilityState !== "visible") return;
  try {
    const fresh = await loadData();
    if (fresh.predictions.generated_at === data.predictions.generated_at) return;
    data = fresh;
    if (route().tab === "vysledky") render();
    announce();
  } catch {
    /* bez siete ostanú posledné dáta */
  }
}

async function start(): Promise<void> {
  app.innerHTML = `<p class="empty" role="status">Načítavam…</p>`;
  try {
    data = await loadData();
    render();
    announce();
  } catch (e) {
    app.innerHTML = `<div class="empty" role="alert"><p>Dáta sa nepodarilo načítať.</p>
      <p class="small muted">${String(e instanceof Error ? e.message : e)}</p>
      <button type="button" class="button" id="retry">Skúsiť znova</button></div>`;
    document.getElementById("retry")?.addEventListener("click", start);
  }
}

/* Jemné 3D naklonenie karty za myšou (len počítač s myšou, nie pri obmedzení pohybu). Jeden poslucháč, nič na mobile. */
function tilt(): void {
  if (!matchMedia("(hover: hover) and (pointer: fine)").matches || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  let card: HTMLElement | null = null;
  let frame = 0;
  app.addEventListener("pointermove", (e) => {
    const el = (e.target as HTMLElement).closest<HTMLElement>(".match, .tiprow, .teamrow");
    if (card && card !== el) {
      card.style.removeProperty("--rx");
      card.style.removeProperty("--ry");
    }
    card = el;
    if (!el || frame) return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      const r = el.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
      el.style.setProperty("--rx", `${(-y * 5).toFixed(2)}deg`);
      el.style.setProperty("--ry", `${(x * 6).toFixed(2)}deg`);
    });
  });
  app.addEventListener("pointerleave", () => {
    card?.style.removeProperty("--rx");
    card?.style.removeProperty("--ry");
    card = null;
  });
}

window.addEventListener("hashchange", render);
document.addEventListener("visibilitychange", refresh);
window.setInterval(refresh, 5 * 60_000);
tilt();
start();

if (import.meta.env.PROD && "serviceWorker" in navigator) {
  navigator.serviceWorker.register("./sw.js").catch(() => undefined);
}
