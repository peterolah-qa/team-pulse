/* Upozornenia v appke: po otvorení (aj po návrate z pozadia) ukáže krátke správy o zápasoch,
   ktoré od poslednej návštevy skončili, a na záložke Výsledky počet ešte nevidených výsledkov.
   Pamäť je len v tomto zariadení (localStorage). Keď nie je dostupná, appka funguje ďalej bez upozornení. */
import type { AppData, Result } from "./data";
import { esc } from "./ui";
import { tipResult } from "./views/result";

const NOTIFIED = "tp-notified";
const VIEWED = "tp-viewed";
const MAX_TOASTS = 3;
const TOAST_MS = 7000;
const KEEP = 400; // koľko posledných zápasov si pamätať

function load(key: string): Set<string> | null {
  try {
    const raw = localStorage.getItem(key);
    return raw ? new Set(JSON.parse(raw) as string[]) : null;
  } catch {
    return null;
  }
}

function save(key: string, ids: Set<string>): void {
  try {
    localStorage.setItem(key, JSON.stringify([...ids].slice(-KEEP)));
  } catch {
    /* súkromné okno alebo plné úložisko: upozornenia sa len nezapamätajú */
  }
}

const results = (d: AppData): Result[] => d.predictions.results ?? [];

/* Nové výsledky od posledného upozornenia. Pri úplne prvom otvorení appky nič neukáže (len si zapamätá stav). */
export function takeNew(d: AppData): Result[] {
  const ids = results(d).map((r) => r.game_id);
  const notified = load(NOTIFIED);
  save(NOTIFIED, new Set([...(notified ?? []), ...ids]));
  if (!notified) {
    if (!load(VIEWED)) save(VIEWED, new Set(ids));
    return [];
  }
  return results(d).filter((r) => !notified.has(r.game_id));
}

/* Počet výsledkov, ktoré si používateľ ešte nepozrel na obrazovke Výsledky. */
export function unseen(d: AppData): number {
  const viewed = load(VIEWED);
  if (!viewed) return 0;
  return results(d).filter((r) => !viewed.has(r.game_id)).length;
}

export function markViewed(d: AppData): void {
  save(VIEWED, new Set([...(load(VIEWED) ?? []), ...results(d).map((r) => r.game_id)]));
}

export function updateBadge(d: AppData): void {
  const tab = document.querySelector<HTMLAnchorElement>('.tabbar a[data-tab="vysledky"]');
  if (!tab) return;
  const n = unseen(d);
  let badge = tab.querySelector<HTMLElement>(".badge");
  if (!n) return badge?.remove();
  if (!badge) {
    badge = document.createElement("span");
    badge.className = "badge";
    tab.append(badge);
  }
  const word = n === 1 ? "nový výsledok" : n < 5 ? "nové výsledky" : "nových výsledkov";
  badge.innerHTML = `<span aria-hidden="true">${n}</span><span class="sr-only">, ${n} ${word}</span>`;
}

function toastHtml(r: Result): string {
  const t = tipResult(r);
  const score = `${esc(r.away)} ${r.pts_away} : ${r.pts_home} ${esc(r.home)}`;
  if (!t) return `<a class="toast none" href="#/vysledok/${esc(r.game_id)}"><span class="t-ico" aria-hidden="true">●</span><span><b>Koniec zápasu</b> ${score}</span></a>`;
  return `<a class="toast ${t.hit ? "hit" : "miss"}" href="#/vysledok/${esc(r.game_id)}"><span class="t-ico" aria-hidden="true">${t.hit ? "✓" : "✗"}</span>
    <span><b>Tip ${t.hit ? "vyšiel" : "nevyšiel"}</b> ${score} <span class="t-sub">tip ${esc(t.fav)} ${t.p} %</span></span></a>`;
}

export function showToasts(list: Result[]): void {
  const box = document.getElementById("toasts");
  if (!box || !list.length) return;
  const sorted = [...list].sort((a, b) => (b.tipoff_utc ?? b.date).localeCompare(a.tipoff_utc ?? a.date));
  const shown = sorted.slice(0, MAX_TOASTS).map(toastHtml);
  if (sorted.length > MAX_TOASTS)
    shown.push(`<a class="toast more" href="#/vysledky"><span class="t-ico" aria-hidden="true">+</span><span><b>Ďalšie výsledky: ${sorted.length - MAX_TOASTS}</b></span></a>`);
  box.innerHTML = shown.join("");
  const clear = () => (box.innerHTML = "");
  box.querySelectorAll("a").forEach((a) => a.addEventListener("click", clear));
  window.setTimeout(clear, TOAST_MS);
}
