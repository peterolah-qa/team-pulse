import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { listMode, nflReady, nhlReady, open, serveData, visitedBefore, withResults } from "./helpers";

/* Automatická kontrola prístupnosti (WCAG 2.1 A + AA) na každej obrazovke. */
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
  "nhl-zapasy-zoznam": "#/nhl/",
  "nhl-tipy": "#/nhl/tipy",
  "nhl-vysledky": "#/nhl/vysledky",
  "nhl-zapas": "#/nhl/zapas/2026020201",
  "nhl-teamy": "#/nhl/teamy",
  "nhl-model": "#/nhl/model",
  "nfl-zapasy": "#/nfl/",
  "nfl-zapasy-zoznam": "#/nfl/",
  "nfl-tipy": "#/nfl/tipy",
  "nfl-vysledky": "#/nfl/vysledky",
  "nfl-zapas": "#/nfl/zapas/2026_08_CAR_GB",
  "nfl-teamy": "#/nfl/teamy",
  "nfl-model": "#/nfl/model",
};

for (const [name, hash] of Object.entries(SCREENS)) {
  test(`a11y: ${name}`, async ({ page }) => {
    if (name.endsWith("-zoznam")) await listMode(page);
    await serveData(page, { predictions: withResults });
    await open(page, hash);
    if (hash.startsWith("#/nhl")) await nhlReady(page); // NHL a NFL sa načítajú až po otvorení
    if (hash.startsWith("#/nfl")) await nflReady(page);
    const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const summary = result.violations.map((v) => `${v.id}: ${v.nodes.length}× ${v.help}`);
    expect(result.passes.length).toBeGreaterThan(10); // axe naozaj bežal
    expect(summary).toEqual([]);
  });
}

test("a11y: upozornenia na dohrané zápasy a číslo na záložke Výsledky", async ({ page }) => {
  await serveData(page, { predictions: withResults });
  await visitedBefore(page, ["0012600050"]);
  await open(page);
  await page.locator("#toasts .toast").first().waitFor();
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(result.violations.map((v) => `${v.id}: ${v.nodes.length}× ${v.help}`)).toEqual([]);
});

test("a11y: rozbaľovacie podrobnosti sa ovládajú klávesnicou", async ({ page }) => {
  await serveData(page, { predictions: withResults });
  await open(page, "#/zapas/0022600001");
  const summary = page.locator("details.more summary");
  await summary.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("details.more")).toHaveAttribute("open", "");
});
