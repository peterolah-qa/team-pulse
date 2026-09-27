/* Vstupný bod: načíta dáta, jednoduchý router (#/…), prepínanie obrazoviek. */
// Len latinka + latin-ext (slovenské znaky), nie thai/devanagari – menší download.
import "@fontsource/chakra-petch/latin-700.css";
import "@fontsource/chakra-petch/latin-ext-700.css";
import "@fontsource/chakra-petch/latin-700-italic.css";
import "@fontsource/chakra-petch/latin-ext-700-italic.css";
import "@fontsource/rajdhani/latin-500.css";
import "@fontsource/rajdhani/latin-ext-500.css";
import "@fontsource/rajdhani/latin-600.css";
import "@fontsource/rajdhani/latin-ext-600.css";
import "@fontsource/rajdhani/latin-700.css";
import "@fontsource/rajdhani/latin-ext-700.css";
import "./style.css";

import { loadData, type AppData } from "./data";
import { gameView } from "./views/game";
import { modelView } from "./views/model";
import { teamsView, teamView } from "./views/team";
import { todayView } from "./views/today";
import { bindWhatIf, whatIfView } from "./views/whatif";

const app = document.getElementById("app")!;
let data: AppData | null = null;

function route(): { tab: string; html: string; title: string } {
  const [, page = "", arg = ""] = (location.hash || "#/").split("/");
  const d = data!;
  switch (page) {
    case "zapas":
      return { tab: "dnes", html: gameView(d, decodeURIComponent(arg)), title: "Zápas" };
    case "teamy":
      return { tab: "teamy", html: teamsView(d), title: "Teamy" };
    case "team":
      return { tab: "teamy", html: teamView(d, decodeURIComponent(arg)), title: arg };
    case "cokeby":
      return { tab: "cokeby", html: whatIfView(d, arg ? decodeURIComponent(arg) : undefined), title: "Čo keby" };
    case "model":
      return { tab: "model", html: modelView(d), title: "Model" };
    default:
      return { tab: "dnes", html: todayView(d), title: "Dnes" };
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
  bindWhatIf(app);
  window.scrollTo(0, 0);
}

async function start(): Promise<void> {
  app.innerHTML = `<p class="empty" role="status">Načítavam…</p>`;
  try {
    data = await loadData();
    render();
  } catch (e) {
    app.innerHTML = `<div class="empty" role="alert"><p>Dáta sa nepodarilo načítať.</p>
      <p class="small muted">${String(e instanceof Error ? e.message : e)}</p>
      <button type="button" class="button" id="retry">Skúsiť znova</button></div>`;
    document.getElementById("retry")?.addEventListener("click", start);
  }
}

window.addEventListener("hashchange", render);
start();

if (import.meta.env.PROD && "serviceWorker" in navigator) {
  navigator.serviceWorker.register("./sw.js").catch(() => undefined);
}
