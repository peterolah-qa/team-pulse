import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { open, serveData, withResults } from "./helpers";

/* Automatická kontrola prístupnosti (WCAG 2.1 A + AA) na každej obrazovke. */
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
  test(`a11y: ${name}`, async ({ page }) => {
    await serveData(page, { predictions: withResults });
    await open(page, hash);
    const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const summary = result.violations.map((v) => `${v.id}: ${v.nodes.length}× ${v.help}`);
    expect(result.passes.length).toBeGreaterThan(10); // axe naozaj bežal
    expect(summary).toEqual([]);
  });
}

test("a11y: rozbaľovacie podrobnosti sa ovládajú klávesnicou", async ({ page }) => {
  await serveData(page, { predictions: withResults });
  await open(page, "#/zapas/0022600001");
  const summary = page.locator("details.more summary");
  await summary.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("details.more")).toHaveAttribute("open", "");
});
