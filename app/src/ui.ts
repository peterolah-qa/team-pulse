/* Spoločné UI prvky: formátovanie, dátumy v našom čase, farby úrovní, prstenec Pulse. */
import type { Tier } from "./data";

export const TEAM_NAMES: Record<string, string> = {
  ATL: "Atlanta Hawks", BOS: "Boston Celtics", BKN: "Brooklyn Nets", CHA: "Charlotte Hornets",
  CHI: "Chicago Bulls", CLE: "Cleveland Cavaliers", DAL: "Dallas Mavericks", DEN: "Denver Nuggets",
  DET: "Detroit Pistons", GSW: "Golden State Warriors", HOU: "Houston Rockets", IND: "Indiana Pacers",
  LAC: "LA Clippers", LAL: "Los Angeles Lakers", MEM: "Memphis Grizzlies", MIA: "Miami Heat",
  MIL: "Milwaukee Bucks", MIN: "Minnesota Timberwolves", NOP: "New Orleans Pelicans", NYK: "New York Knicks",
  OKC: "Oklahoma City Thunder", ORL: "Orlando Magic", PHI: "Philadelphia 76ers", PHX: "Phoenix Suns",
  POR: "Portland Trail Blazers", SAC: "Sacramento Kings", SAS: "San Antonio Spurs", TOR: "Toronto Raptors",
  UTA: "Utah Jazz", WAS: "Washington Wizards",
};

export const TIERS: Tier[] = ["Silný", "Stabilný", "Oslabený", "Kritický"];
const TIER_CLASS: Record<Tier, string> = { Silný: "t0", Stabilný: "t1", Oslabený: "t2", Kritický: "t3" };
export const tierClass = (t: Tier): string => TIER_CLASS[t];

export const esc = (s: unknown): string =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);

const nf1 = new Intl.NumberFormat("sk-SK", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
export const pct = (p: number): string => `${Math.round(p * 100)} %`;
export const pct1 = (p: number): string => `${nf1.format(p * 100)} %`;
export const num1 = (x: number): string => nf1.format(x);
export const signed = (x: number): string => (x > 0 ? `+${x}` : x < 0 ? `−${Math.abs(x)}` : "0");

/* Pulse sa zobrazuje zaokrúhlený nadol, aby sedel s hranicami úrovní (49,5 = 49 = Oslabený). */
export const pulseNum = (p: number): number => Math.floor(p);

/* Šanca domácich v celých percentách tak, aby hostia + domáci dali vždy presne 100 %. */
export function split(pHome: number): { home: number; away: number } {
  const home = Math.round(pHome * 100);
  return { home, away: 100 - home };
}

export function chip(t: Tier, text: string = t): string {
  return `<span class="chip ${tierClass(t)}">${esc(text)}</span>`;
}

// --- dátumy a časy: všetko v našom čase (zápas o 2:00 v noci patrí k dňu, keď o 2:00 začína) ---

export function parseUtc(s?: string | null): Date | null {
  if (!s) return null;
  const d = new Date(s.includes("T") ? s : s.replace(" ", "T"));
  return isNaN(d.getTime()) ? null : d;
}

const dayKey = (d: Date): string => d.toLocaleDateString("sv-SE"); // yyyy-mm-dd v našom čase

/* Deň zápasu v našom čase. Bez času začiatku ostane americký dátum zápasu. */
export function localDay(utc: string | undefined, usDate: string): string {
  const d = parseUtc(utc);
  return d ? dayKey(d) : usDate;
}

export function time(utc?: string): string {
  const d = parseUtc(utc);
  return d ? d.toLocaleTimeString("sk-SK", { hour: "2-digit", minute: "2-digit" }) : "";
}

const noon = (key: string): Date => new Date(`${key}T12:00:00`);

/* „sobota 10. 10.“ */
export function longDate(key: string): string {
  const d = noon(key);
  return `${d.toLocaleDateString("sk-SK", { weekday: "long" })} ${d.getDate()}. ${d.getMonth() + 1}.`;
}

/* „so 10. 10.“ do riadkov zoznamu */
export function shortDate(key: string): string {
  const d = noon(key);
  return `${d.toLocaleDateString("sk-SK", { weekday: "short" })} ${d.getDate()}. ${d.getMonth() + 1}.`;
}

/* Nadpis dňa: Dnes / Zajtra / Včera, inak deň v týždni. */
export function dayTitle(key: string, now: Date = new Date()): { title: string; date: string } {
  const shift = (n: number) => dayKey(new Date(now.getFullYear(), now.getMonth(), now.getDate() + n, 12));
  const rel: Record<string, string> = { [shift(0)]: "Dnes", [shift(1)]: "Zajtra", [shift(-1)]: "Včera" };
  const date = longDate(key);
  return rel[key] ? { title: rel[key], date } : { title: date.charAt(0).toUpperCase() + date.slice(1), date: "" };
}

export function when(iso: string): string {
  const d = parseUtc(iso);
  return d ? d.toLocaleString("sk-SK", { day: "numeric", month: "numeric", hour: "2-digit", minute: "2-digit" }) : "";
}

export function groupBy<T>(items: T[], key: (x: T) => string): [string, T[]][] {
  const out = new Map<string, T[]>();
  for (const it of items) out.set(key(it), [...(out.get(key(it)) ?? []), it]);
  return [...out.entries()];
}

// --- stavebné bloky obrazoviek ---

export function header(title: string, sub = "", back?: { href: string; label: string }): string {
  return `<header class="top">
    ${back ? `<a class="back" href="${back.href}">‹ ${esc(back.label)}</a>` : `<span class="brand" aria-hidden="true">Team Pulse</span>`}
    <h1>${title}</h1>${sub ? `<p class="sub">${sub}</p>` : ""}</header>`;
}

export function dayHeading(key: string, count: number, word: [string, string, string]): string {
  const { title, date } = dayTitle(key);
  const n = count === 1 ? word[0] : count < 5 ? word[1] : word[2];
  return `<h2 class="day"><span>${esc(title)}</span>${date ? ` <span class="day-date">${esc(date)}</span>` : ""}<span class="day-n">${count} ${n}</span></h2>`;
}

export const teamLink = (abbr: string): string =>
  `<a class="abbr" href="#/team/${esc(abbr)}">${esc(abbr)}</a>`;

export function ring(pulse: number, t: Tier, size = 88): string {
  const stroke = size * 0.09;
  const r = size / 2 - stroke - 2;
  const c = 2 * Math.PI * r;
  const off = c * (1 - Math.max(0, Math.min(100, pulse)) / 100);
  const mid = size / 2;
  return `<svg class="ring ${tierClass(t)}" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}"
      role="img" aria-label="Pulse ${pulseNum(pulse)} zo 100, ${esc(t)}">
    <circle cx="${mid}" cy="${mid}" r="${r}" class="ring-bg" stroke-width="${stroke}" fill="none"/>
    <circle cx="${mid}" cy="${mid}" r="${r}" class="ring-fg" stroke-width="${stroke}" fill="none"
      stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${off.toFixed(1)}" transform="rotate(-90 ${mid} ${mid})"/>
    <text x="${mid}" y="${mid + size * 0.11}" text-anchor="middle" class="ring-num" font-size="${size * 0.32}">${pulseNum(pulse)}</text>
  </svg>`;
}
