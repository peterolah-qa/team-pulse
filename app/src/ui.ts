/* Spoločné UI prvky: formátovanie, dátumy v našom čase, farby úrovní, prstenec Pulse. */
import type { Sport, Tier } from "./data";

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

/* Farby teamov (dve hlavné farby dresu) – len farby, žiadne logá. */
export const TEAM_COLORS: Record<string, [string, string]> = {
  ATL: ["#e03a3e", "#c4d600"], BOS: ["#007a33", "#ba9653"], BKN: ["#1b1b1b", "#ffffff"], CHA: ["#1d1160", "#00788c"],
  CHI: ["#ce1141", "#1b1b1b"], CLE: ["#860038", "#fdbb30"], DAL: ["#00538c", "#b8c4ca"], DEN: ["#0e2240", "#fec524"],
  DET: ["#c8102e", "#1d42ba"], GSW: ["#1d428a", "#ffc72c"], HOU: ["#ce1141", "#c4ced4"], IND: ["#002d62", "#fdbb30"],
  LAC: ["#c8102e", "#1d428a"], LAL: ["#552583", "#fdb927"], MEM: ["#5d76a9", "#12173f"], MIA: ["#98002e", "#f9a01b"],
  MIL: ["#00471b", "#eee1c6"], MIN: ["#0c2340", "#78be20"], NOP: ["#0c2340", "#c8102e"], NYK: ["#006bb6", "#f58426"],
  OKC: ["#007ac1", "#ef3b24"], ORL: ["#0077c0", "#c4ced4"], PHI: ["#006bb6", "#ed174c"], PHX: ["#1d1160", "#e56020"],
  POR: ["#e03a3e", "#1b1b1b"], SAC: ["#5a2d81", "#63727a"], SAS: ["#c4ced4", "#1b1b1b"], TOR: ["#ce1141", "#a1a1a4"],
  UTA: ["#4b2a87", "#f9a01b"], WAS: ["#002b5c", "#e31837"],
};

export const NHL_NAMES: Record<string, string> = {
  ANA: "Anaheim Ducks", BOS: "Boston Bruins", BUF: "Buffalo Sabres", CAR: "Carolina Hurricanes",
  CBJ: "Columbus Blue Jackets", CGY: "Calgary Flames", CHI: "Chicago Blackhawks", COL: "Colorado Avalanche",
  DAL: "Dallas Stars", DET: "Detroit Red Wings", EDM: "Edmonton Oilers", FLA: "Florida Panthers",
  LAK: "Los Angeles Kings", MIN: "Minnesota Wild", MTL: "Montréal Canadiens", NJD: "New Jersey Devils",
  NSH: "Nashville Predators", NYI: "New York Islanders", NYR: "New York Rangers", OTT: "Ottawa Senators",
  PHI: "Philadelphia Flyers", PIT: "Pittsburgh Penguins", SEA: "Seattle Kraken", SJS: "San Jose Sharks",
  STL: "St. Louis Blues", TBL: "Tampa Bay Lightning", TOR: "Toronto Maple Leafs", UTA: "Utah Mammoth",
  VAN: "Vancouver Canucks", VGK: "Vegas Golden Knights", WPG: "Winnipeg Jets", WSH: "Washington Capitals",
};

/* NHL farby dresov (skratky sa s NBA prekrývajú: BOS, DAL, DET, MIN, PHI, TOR, UTA, CHI). */
export const NHL_COLORS: Record<string, [string, string]> = {
  ANA: ["#f47a38", "#b9975b"], BOS: ["#ffb81c", "#1b1b1b"], BUF: ["#003087", "#ffb81c"], CAR: ["#ce1126", "#1b1b1b"],
  CBJ: ["#002654", "#ce1126"], CGY: ["#c8102e", "#f1be48"], CHI: ["#cf0a2c", "#1b1b1b"], COL: ["#6f263d", "#236192"],
  DAL: ["#006847", "#8f8f8c"], DET: ["#ce1126", "#ffffff"], EDM: ["#041e42", "#ff4c00"], FLA: ["#041e42", "#c8102e"],
  LAK: ["#1b1b1b", "#a2aaad"], MIN: ["#154734", "#a6192e"], MTL: ["#af1e2d", "#192168"], NJD: ["#ce1126", "#1b1b1b"],
  NSH: ["#ffb81c", "#041e42"], NYI: ["#00539b", "#f47d30"], NYR: ["#0038a8", "#ce1126"], OTT: ["#1b1b1b", "#c52032"],
  PHI: ["#f74902", "#1b1b1b"], PIT: ["#1b1b1b", "#fcb514"], SEA: ["#001628", "#99d9d9"], SJS: ["#006d75", "#ea7200"],
  STL: ["#002f87", "#fcb514"], TBL: ["#002868", "#ffffff"], TOR: ["#00205b", "#ffffff"], UTA: ["#6cace4", "#1b1b1b"],
  VAN: ["#00205b", "#00843d"], VGK: ["#b4975a", "#333f42"], WPG: ["#041e42", "#ac162c"], WSH: ["#c8102e", "#041e42"],
};

export const teamName = (abbr: string, sport: Sport = "nba"): string => (sport === "nhl" ? NHL_NAMES : TEAM_NAMES)[abbr] ?? abbr;

/* 3D minca vo farbách teamu (dvojfarebný dres, lesk a hĺbka). S textom = veľká minca v detaile. */
export function coin(abbr: string, label = false, sport: Sport = "nba"): string {
  const [c1, c2] = (sport === "nhl" ? NHL_COLORS : TEAM_COLORS)[abbr] ?? ["#3a3f55", "#8a90a8"];
  return `<span class="coin${label ? " big" : ""}" style="--c1:${c1};--c2:${c2}" aria-hidden="true">${label ? esc(abbr) : ""}</span>`;
}

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

/* Hlavička obrazovky. Hlavné obrazovky majú vedľa značky prepínač športu (doplní ho main.ts). */
export function header(title: string, sub = "", back?: { href: string; label: string }): string {
  return `<header class="top">
    ${back ? `<a class="back" href="${back.href}">‹ ${esc(back.label)}</a>` : `<div class="brandrow"><span class="brand" aria-hidden="true">Team Pulse</span><span data-sport-switch></span></div>`}
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

/* Tenký pruh šancí pod zápasom v zozname: hostia vľavo, domáci vpravo, favorit zlatý (ako v detaile).
   Len doplnok k číslam vedľa, preto aria-hidden. */
export function oddsBar(pHome: number): string {
  const { away } = split(pHome);
  return `<span class="mbar ${pHome > 0.5 ? "home-fav" : "away-fav"}" aria-hidden="true"><i style="width:${away}%"></i></span>`;
}

/* Malý graf formy (Pulse po zápasoch). Posledný bod zvýraznený, čísla sú aj v popise pre čítačky. */
export function sparkline(values: number[], t: Tier, label: string, w = 72, h = 24): string {
  if (values.length < 2) return "";
  const pad = 4;
  const lo = Math.min(...values), hi = Math.max(...values);
  const span = Math.max(hi - lo, 10); // malý rozptyl nech nevyzerá ako dráma
  const mid = (lo + hi) / 2;
  const x = (i: number) => pad + (i / (values.length - 1)) * (w - 2 * pad);
  const y = (v: number) => h / 2 - ((v - mid) / span) * (h - 2 * pad);
  const pts = values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const last = values.length - 1;
  return `<svg class="spark ${tierClass(t)}" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(label)}">
    <polyline points="${pts}"/><circle cx="${x(last).toFixed(1)}" cy="${y(values[last]).toFixed(1)}" r="3"/></svg>`;
}
