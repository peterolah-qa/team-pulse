/* Sledované zápasy: tlačidlo „Sledovať zápas“ v detaile. Keď sa sledovaný zápas dohrá, appka pri ďalšom
   otvorení (alebo návrate z pozadia) ukáže výsledok a či tip vyšiel. Pamäť je len v tomto zariadení
   (localStorage). Push notifikácie mimo appky to nie sú – tie by potrebovali server. */
import type { NhlResult, Sport } from "./data";
import { esc, split } from "./ui";

const KEY = "tp-follow";
const KEEP = 50;

export interface Followed {
  sport: Sport;
  id: string;
  label: string; // „SJS @ MTL“
  since: string; // kedy začal sledovať (ISO)
}

function load(): Followed[] {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? "[]") as unknown;
    return Array.isArray(raw) ? (raw as Followed[]).filter((f) => f && typeof f.id === "string") : [];
  } catch {
    return [];
  }
}

function save(list: Followed[]): boolean {
  try {
    localStorage.setItem(KEY, JSON.stringify(list.slice(-KEEP)));
    return true;
  } catch {
    return false; // súkromné okno: sledovanie sa nedá zapamätať
  }
}

export const followed = (sport?: Sport): Followed[] => load().filter((f) => !sport || f.sport === sport);
export const isFollowed = (sport: Sport, id: string): boolean => load().some((f) => f.sport === sport && f.id === id);

/* Prepne sledovanie. Vráti nový stav, alebo null, keď sa nedá uložiť. */
export function toggle(sport: Sport, id: string, label: string): boolean | null {
  const list = load();
  const on = !list.some((f) => f.sport === sport && f.id === id);
  const next = on ? [...list, { sport, id, label, since: new Date().toISOString() }] : list.filter((f) => !(f.sport === sport && f.id === id));
  return save(next) ? on : null;
}

/* Dohraté sledované NHL zápasy: upozornenia a odstránenie zo sledovaných. */
export function settleNhl(results: NhlResult[]): string[] {
  const list = load();
  const done = new Map(results.map((r) => [r.game_id, r]));
  const hits = list.filter((f) => f.sport === "nhl" && done.has(f.id));
  if (!hits.length) return [];
  save(list.filter((f) => !(f.sport === "nhl" && done.has(f.id))));
  return hits.map((f) => {
    const r = done.get(f.id)!;
    const extra = r.last_period === "OT" ? " pp" : r.last_period === "SO" ? " sn" : "";
    const score = `${esc(r.away)} ${r.goals_away} : ${r.goals_home} ${esc(r.home)}${extra}`;
    if (r.p_home == null)
      return `<a class="toast info" href="#/nhl/vysledky"><span class="t-ico" aria-hidden="true">●</span><span><b>Sledovaný zápas skončil</b> ${score}</span></a>`;
    const homeFav = r.p_home > 0.5;
    const hit = homeFav === r.goals_home > r.goals_away;
    const { home, away } = split(r.p_home);
    const tip = `${esc(homeFav ? r.home : r.away)} ${homeFav ? home : away} %`;
    return `<a class="toast ${hit ? "hit" : "miss"}" href="#/nhl/vysledky"><span class="t-ico" aria-hidden="true">${hit ? "✓" : "✗"}</span>
      <span><b>Tip ${hit ? "vyšiel" : "nevyšiel"}</b> ${score} <span class="t-sub">sledovaný zápas · tip ${tip}</span></span></a>`;
  });
}
