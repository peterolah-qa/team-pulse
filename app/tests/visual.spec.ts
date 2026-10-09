import { expect, test } from "@playwright/test";
import { open, serveData, withResults } from "./helpers";

/* Vizuálna regresia: porovná obrazovky s uloženými screenshotmi (tests/visual.spec.ts-snapshots).
   Po zámernej zmene dizajnu: npm run test:update-snapshots */
const SCREENS = {
  zapasy: "#/",
  tipy: "#/tipy",
  vysledky: "#/vysledky",
  vysledok: "#/vysledok/0022600900",
  zapas: "#/zapas/0022600001",
  team: "#/team/PHI",
  teamy: "#/teamy",
  model: "#/model",
};

for (const [name, hash] of Object.entries(SCREENS)) {
  test(`vzhľad: ${name}`, async ({ page }) => {
    await serveData(page, { predictions: withResults });
    await open(page, hash);
    await page.evaluate(() => document.fonts.ready);
    // spodná lišta je fixed – pri screenshote celej stránky ju dáme na koniec, nech neprekrýva obsah
    await page.addStyleTag({ content: ".tabbar { position: static !important; transform: none !important; margin: 16px auto 0; }" });
    await expect(page).toHaveScreenshot(`${name}.png`, { fullPage: true });
  });
}
