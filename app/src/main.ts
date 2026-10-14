/* Vstupný bod: načíta dáta, jednoduchý router (#/…), prepínanie obrazoviek. */
// Len latinka + latin-ext (slovenské znaky), nie thai/devanagari – menší download.
import "@fontsource/chakra-petch/latin-700.css";
import "@fontsource/chakra-petch/latin-ext-700.css";
import "@fontsource/barlow/latin-400.css";
import "@fontsource/barlow/latin-ext-400.css";
import "@fontsource/barlow/latin-600.css";
import "@fontsource/barlow/latin-ext-600.css";
import "./style.css";

import { loadData, loadNhl, type AppData, type NhlData, type Sport } from "./data";
import { markViewed, showToasts, takeNew, updateBadge } from "./notify";
import { esc, header } from "./ui";
import { gameView } from "./views/game";
import { gamesView } from "./views/games";
import { modelView } from "./views/model";
import { nhlGamesView, nhlGameView, nhlModelView, nhlResultsView, nhlTeamsView, nhlTipsView } from "./views/nhl";
import { resultsView, resultView } from "./views/result";
import { teamsView, teamView } from "./views/team";
import { tipsView } from "./views/tips";

const app = document.getElementById("app")!;
let data: AppData | null = null;
let nhl: NhlData | null = null; // NHL sa načíta až pri prvom otvorení
let nhlError: string | null = null;
let nhlLoading: Promise<void> | null = null;

const SPORT_KEY = "tp-sport";
/* záložka → cesta v adrese (bez športu) */
const TAB_PATH: Record<string, string> = { zapasy: "", tipy: "tipy", vysledky: "vysledky", teamy: "teamy", model: "model" };
const PATH_TAB: Record<string, string> = Object.fromEntries(Object.entries(TAB_PATH).map(([tab, path]) => [path, tab]));
const TITLES: Record<string, string> = { zapasy: "Zápasy", tipy: "Tipy", vysledky: "Výsledky", teamy: "Teamy", model: "Model" };

interface Route {
  sport: Sport;
  tab: string;
  html: string;
  title: string;
  wide: boolean; // zoznamy sa na širokej obrazovke rozložia do dvoch stĺpcov, detaily ostanú úzke
}

/* #/tipy = NBA, #/nhl/tipy = NHL. Staré odkazy bez športu ostávajú NBA. */
function parse(): { sport: Sport; page: string; arg: string } {
  const parts = (location.hash || "#/").split("/");
  if (parts[1] === "nhl") return { sport: "nhl", page: parts[2] ?? "", arg: decodeURIComponent(parts[3] ?? "") };
  return { sport: "nba", page: parts[1] ?? "", arg: decodeURIComponent(parts[2] ?? "") };
}

function nbaRoute(page: string, id: string): Omit<Route, "sport"> {
  const d = data!;
  switch (page) {
    case "zapas":
      return { tab: "zapasy", html: gameView(d, id), title: "Zápas", wide: false };
    case "cokeby": // staré odkazy na „Čo keby“ vedú na detail zápasu
      return id ? { tab: "zapasy", html: gameView(d, id), title: "Zápas", wide: false } : { tab: "zapasy", html: gamesView(d), title: "Zápasy", wide: true };
    case "tipy":
      return { tab: "tipy", html: tipsView(d), title: "Tipy", wide: true };
    case "vysledky":
      return { tab: "vysledky", html: resultsView(d), title: "Výsledky", wide: true };
    case "vysledok":
      return { tab: "vysledky", html: resultView(d, id), title: "Výsledok", wide: false };
    case "teamy":
      return { tab: "teamy", html: teamsView(d), title: "Teamy", wide: true };
    case "team":
      return { tab: "teamy", html: teamView(d, id), title: id, wide: false };
    case "model":
      return { tab: "model", html: modelView(d), title: "Model", wide: false };
    default:
      return { tab: "zapasy", html: gamesView(d), title: "Zápasy", wide: true };
  }
}

function nhlRoute(page: string, id: string): Omit<Route, "sport"> {
  const tab = PATH_TAB[page] ?? "zapasy"; // detail zápasu patrí pod Zápasy
  const title = TITLES[tab];
  if (!nhl) {
    const html = nhlError
      ? `${header(title)}<div class="empty" role="alert"><p>NHL dáta sa nepodarilo načítať.</p><p class="small muted">${esc(nhlError)}</p>
          <button type="button" class="button" id="retry-nhl">Skúsiť znova</button></div>`
      : `${header(title)}<p class="empty" role="status">Načítavam NHL…</p>`;
    return { tab, html, title, wide: false };
  }
  const n = nhl;
  switch (page) {
    case "zapas":
      return { tab, html: nhlGameView(n, id), title: "Zápas", wide: false };
    case "tipy":
      return { tab, html: nhlTipsView(n), title, wide: true };
    case "vysledky":
      return { tab, html: nhlResultsView(n), title, wide: true };
    case "teamy":
      return { tab, html: nhlTeamsView(n), title, wide: true };
    case "model":
      return { tab, html: nhlModelView(n), title, wide: false };
    default:
      return { tab, html: nhlGamesView(n), title, wide: true };
  }
}

function route(): Route {
  const { sport, page, arg } = parse();
  return { sport, ...(sport === "nhl" ? nhlRoute(page, arg) : nbaRoute(page, arg)) };
}

function ensureNhl(): void {
  if (nhl || nhlError || nhlLoading) return;
  nhlLoading = loadNhl()
    .then((n) => (nhl = n))
    .catch((e) => (nhlError = String(e instanceof Error ? e.message : e)))
    .then(() => {
      nhlLoading = null;
      if (parse().sport === "nhl") render();
    });
}

/* Prepínač NBA / NHL vedľa značky: rovnaká záložka v druhom športe. */
function sportSwitch(r: Route): string {
  const path = TAB_PATH[r.tab] ?? "";
  const link = (s: Sport, label: string) =>
    `<a href="#/${s === "nhl" ? "nhl/" : ""}${path}"${r.sport === s ? ' aria-current="page"' : ""}>${label}</a>`;
  return `<nav class="sport" aria-label="Šport">${link("nba", "NBA")}${link("nhl", `NHL <span class="beta">beta</span>`)}</nav>`;
}

function saveSport(s: Sport): void {
  try {
    localStorage.setItem(SPORT_KEY, s);
  } catch {
    /* bez úložiska si appka šport len nezapamätá */
  }
}

/* Počet nových výsledkov na záložke patrí k NBA (upozornenia sú zatiaľ len pre NBA). */
function badge(): void {
  if (!data) return;
  if (parse().sport === "nba") updateBadge(data);
  else document.querySelector(".tabbar .badge")?.remove();
}

function render(): void {
  if (!data) return;
  const r = route();
  if (r.sport === "nhl") ensureNhl();
  app.innerHTML = r.html;
  app.dataset.layout = r.wide ? "wide" : "narrow";
  document.body.dataset.sport = r.sport;
  app.querySelector("[data-sport-switch]")?.replaceWith(document.createRange().createContextualFragment(sportSwitch(r)));
  document.getElementById("retry-nhl")?.addEventListener("click", () => {
    nhlError = null;
    render();
  });
  document.title = `${r.sport === "nhl" ? "NHL · " : ""}${r.title} · Team Pulse`;
  const prefix = r.sport === "nhl" ? "#/nhl/" : "#/";
  document.querySelectorAll<HTMLAnchorElement>(".tabbar a").forEach((a) => {
    a.href = prefix + (TAB_PATH[a.dataset.tab ?? ""] ?? "");
    if (a.dataset.tab === r.tab) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  saveSport(r.sport);
  if (r.sport === "nba" && r.tab === "vysledky") markViewed(data);
  badge();
  window.scrollTo(0, 0);
}

/* Nové dáta: upozornenia na dohrané zápasy a číslo na záložke Výsledky. */
function announce(): void {
  if (!data) return;
  showToasts(takeNew(data));
  badge();
}

/* Po návrate appky z pozadia stiahne čerstvé dáta (zobrazí sa pri ďalšom kliknutí) a ukáže, čo skončilo. */
async function refresh(): Promise<void> {
  if (!data || document.visibilityState !== "visible") return;
  try {
    if (nhl) nhl = await loadNhl().catch(() => nhl);
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
  // nainštalovaná appka (bez # v adrese) sa otvorí v naposledy zvolenom športe
  try {
    if (!location.hash && localStorage.getItem(SPORT_KEY) === "nhl") history.replaceState(null, "", "#/nhl/");
  } catch {
    /* bez úložiska ostane NBA */
  }
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
