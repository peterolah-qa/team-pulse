import { expect, test } from "@playwright/test";
import { listMode, nflReady, nhlReady, open, serveData, withResults } from "./helpers";

/* Vizuálna regresia: porovná obrazovky s uloženými screenshotmi (tests/visual.spec.ts-snapshots).
   Po zámernej zmene dizajnu: npm run test:update-snapshots */
const SCREENS = {
  zapasy: "#/",
  "zapasy-zoznam": "#/",
  tipy: "#/tipy",
  vysledky: "#/vysledky",
  vysledok: "#/vysledok/0022600900",
  zapas: "#/zapas/0022600001",
  team: "#/team/PHI",
  teamy: "#/teamy",
  model: "#/model",
  "nhl-zapasy": "#/nhl/",
  "nhl-tipy": "#/nhl/tipy",
  "nhl-zapas": "#/nhl/zapas/2026020201",
  "nfl-zapasy": "#/nfl/",
  "nfl-zapas": "#/nfl/zapas/2026_08_CAR_GB",
};
/* svetlá téma (podľa systému) na dvoch typických obrazovkách */
const LIGHT = { "zapasy-svetla": "#/", "zapas-svetla": "#/zapas/0022600001" };

for (const [name, hash] of [...Object.entries(SCREENS), ...Object.entries(LIGHT)]) {
  test(`vzhľad: ${name}`, async ({ page }) => {
    if (name in LIGHT) await page.emulateMedia({ colorScheme: "light" });
    if (name.endsWith("-zoznam")) await listMode(page);
    await serveData(page, { predictions: withResults });
    await open(page, hash);
    if (hash.startsWith("#/nhl")) await nhlReady(page);
    if (hash.startsWith("#/nfl")) await nflReady(page);
    await page.evaluate(() => document.fonts.ready);
    // spodná lišta je fixed – pri screenshote celej stránky ju dáme na koniec, nech neprekrýva obsah
    await page.addStyleTag({
      content:
        ".tabbar, .cta { position: static !important; transform: none !important; margin: 16px auto 0; } #app[data-cta] { padding-bottom: 0; } .dstrip { position: static !important; }",
    });
    await expect(page).toHaveScreenshot(`${name}.png`, { fullPage: true });
  });
}
