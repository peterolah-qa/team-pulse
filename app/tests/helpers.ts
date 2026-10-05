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

export async function open(page: Page, hash = "#/") {
  await page.goto(`/${hash}`);
  await page.locator("header.top").first().waitFor();
}

/* Výsledky posledných dní: jeden zápas so štatistikami hráčov a tipom, jeden z prípravy bez nich. */
export function withResults(p: Json): Json {
  const row = (player: string, min: number, pts: number) => ({ player, min, pts, reb: 7, ast: 5, blk: 1, stl: 2 });
  p.results = [
    { game_id: "0012600050", date: "2026-10-16", kind: "preseason", home: "MIA", away: "ORL", pts_home: 98, pts_away: 104, p_home: null, box: {} },
    {
      game_id: "0022600900", date: "2026-10-19", kind: "regular", home: "DET", away: "BOS", pts_home: 110, pts_away: 104, p_home: 0.62,
      box: {
        DET: [row("Cade Cunningham", 36, 31), row("Jalen Duren", 30, 14), row("Kristaps Porzingis-Longname", 24, 9)],
        BOS: [row("Jayson Tatum", 38, 27), row("Derrick White", 33, 12)],
      },
    },
  ];
  return p;
}
