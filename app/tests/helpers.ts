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
