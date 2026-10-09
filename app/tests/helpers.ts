import { readFileSync } from "node:fs";
import type { Page } from "@playwright/test";

type Json = Record<string, any>;

export function fixture(name: "predictions" | "teams" | "model"): Json {
  return JSON.parse(readFileSync(new URL(`./fixtures/${name}.json`, import.meta.url), "utf8"));
}

/* Podstrčí appke dáta. `edit` môže fixture pred odoslaním upraviť (prázdny deň, hraničný prípad…). */
export async function serveData(page: Page, edit: Partial<Record<"predictions" | "teams" | "model", (j: Json) => Json>> = {}) {
  await page.route("**/data/*.json", async (route) => {
    const name = route.request().url().split("/").pop()!.replace(".json", "") as "predictions" | "teams" | "model";
    const body = (edit[name] ?? ((j) => j))(fixture(name));
    await route.fulfill({ json: body });
  });
}

/* Pevný „teraz“ pre testy: streda 21. 10. 2026 0:30 nášho času, pol hodiny pred prvým zápasom vo fixture.
   Nadpisy Dnes/Zajtra/Včera aj stav „hrá sa“ tak nezávisia od dňa, keď testy bežia. */
export const NOW = new Date("2026-10-21T00:30:00+02:00");

export async function open(page: Page, hash = "#/", now: Date = NOW) {
  await page.clock.setFixedTime(now);
  await page.goto(`/${hash}`);
  await page.locator("header.top").first().waitFor();
}

/* Výsledky posledných dní: tip vyšiel (DET), tip nevyšiel (NYK), príprava bez tipu a bez štatistík. */
export function withResults(p: Json): Json {
  const row = (player: string, min: number, pts: number) => ({ player, min, pts, reb: 7, ast: 5, blk: 1, stl: 2 });
  const bench = Array.from({ length: 3 }, (_, i) => row(`Náhradník DET ${i + 1}`, 6 - i, 2));
  p.results = [
    { game_id: "0012600050", date: "2026-10-16", kind: "preseason", home: "MIA", away: "ORL", pts_home: 98, pts_away: 104,
      tipoff_utc: "2026-10-16 23:30:00+00:00", p_home: null, box: {} },
    {
      game_id: "0022600900", date: "2026-10-19", kind: "regular", home: "DET", away: "BOS", pts_home: 110, pts_away: 104,
      tipoff_utc: "2026-10-19 23:00:00+00:00", p_home: 0.62,
      box: {
        DET: [row("Cade Cunningham", 36, 31), row("Jalen Duren", 30, 14), row("Kristaps Porzingis-Longname", 24, 9),
          row("Ausar Thompson", 28, 8), row("Tobias Harris", 27, 12), row("Malik Beasley", 22, 15), row("Isaiah Stewart", 18, 6),
          row("Ron Holland", 14, 4), ...bench],
        BOS: [row("Jayson Tatum", 38, 27), row("Derrick White", 33, 12)],
      },
    },
    { game_id: "0022600901", date: "2026-10-19", kind: "regular", home: "NYK", away: "PHI", pts_home: 99, pts_away: 104,
      tipoff_utc: "2026-10-20 00:00:00+00:00", p_home: 0.7,
      box: { NYK: [row("Jalen Brunson", 37, 30)], PHI: [row("Tyrese Maxey", 38, 33)] } },
  ];
  return p;
}
