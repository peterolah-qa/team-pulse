/* Spoločné UI prvky: formátovanie, farby úrovní, prstenec Pulse, chip. */
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

const TIER_CLASS: Record<Tier, string> = { Silný: "t0", Stabilný: "t1", Oslabený: "t2", Kritický: "t3" };

export const esc = (s: unknown): string =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);

const nf1 = new Intl.NumberFormat("sk-SK", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
export const pct = (p: number): string => `${Math.round(p * 100)} %`;
export const pct1 = (p: number): string => `${nf1.format(p * 100)} %`;
export const num1 = (x: number): string => nf1.format(x);
export const signed = (x: number): string => (x > 0 ? `+${x}` : x < 0 ? `−${Math.abs(x)}` : "0");
export const signed1 = (x: number): string => (x > 0 ? `+${nf1.format(x)}` : x < 0 ? `−${nf1.format(-x)}` : "0");

export const tierClass = (t: Tier): string => TIER_CLASS[t];

/* Pulse sa zobrazuje zaokrúhlený nadol, aby sedel s hranicami úrovní (49,5 = 49 = Oslabený). */
export const pulseNum = (p: number): number => Math.floor(p);

export function chip(t: Tier): string {
  return `<span class="chip ${tierClass(t)}">${esc(t.toUpperCase())}</span>`;
}

export function ring(pulse: number, t: Tier, size = 104, label = true): string {
  const stroke = size * 0.085;
  const r = size / 2 - stroke - 3;
  const c = 2 * Math.PI * r;
  const off = c * (1 - Math.max(0, Math.min(100, pulse)) / 100);
  const mid = size / 2;
  return `<svg class="ring ${tierClass(t)}" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}"
      role="img" aria-label="Pulse ${pulseNum(pulse)} z 100, ${esc(t)}">
    <circle cx="${mid}" cy="${mid}" r="${r}" class="ring-bg" stroke-width="${stroke}" fill="none"/>
    <circle cx="${mid}" cy="${mid}" r="${r}" class="ring-fg" stroke-width="${stroke}" fill="none"
      stroke-linecap="butt" stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${off.toFixed(1)}"
      transform="rotate(-90 ${mid} ${mid})"/>
    <text x="${mid}" y="${mid + size * 0.1}" text-anchor="middle" class="ring-num" font-size="${size * 0.3}">${pulseNum(pulse)}</text>
    ${label ? `<text x="${mid}" y="${mid + size * 0.27}" text-anchor="middle" class="ring-lbl" font-size="${size * 0.08}">PULSE</text>` : ""}
  </svg>`;
}

/* Čas začiatku v našom čase. Dátum zápasu je americký, takže keď u nás začína až na druhý deň
   (napr. o 01:00), pridá sa deň v týždni: „ST 01:00“. */
export function tipoff(utc: string, gameDate?: string): string {
  const d = new Date(utc);
  if (isNaN(d.getTime())) return "";
  const time = d.toLocaleTimeString("sk-SK", { hour: "2-digit", minute: "2-digit" });
  const local = d.toLocaleDateString("sv-SE"); // yyyy-mm-dd v lokálnom čase
  if (!gameDate || local === gameDate) return time;
  return `${d.toLocaleDateString("sk-SK", { weekday: "short" }).toUpperCase()} ${time}`;
}

export function dayLabel(iso: string): string {
  const d = new Date(`${iso}T12:00:00`);
  return d.toLocaleDateString("sk-SK", { weekday: "short", day: "numeric", month: "numeric" }).toUpperCase();
}

export function when(iso: string): string {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? "" : d.toLocaleString("sk-SK", { day: "numeric", month: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function header(kicker: string, title: string, aside = ""): string {
  return `<header class="top"><div><div class="kicker">${esc(kicker)}</div><h1>${title}</h1></div>
    ${aside ? `<div class="aside">${aside}</div>` : ""}</header>`;
}

export const teamLink = (abbr: string): string =>
  `<a class="abbr" href="#/team/${esc(abbr)}" aria-label="${esc(TEAM_NAMES[abbr] ?? abbr)}">${esc(abbr)}</a>`;
