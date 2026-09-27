import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { open, serveData } from "./helpers";

/* Automatická kontrola prístupnosti (WCAG 2.1 A + AA) na každej obrazovke. */
const SCREENS = {
  dnes: "#/",
  zapas: "#/zapas/0022600001",
  team: "#/team/PHI",
  teamy: "#/teamy",
  cokeby: "#/cokeby",
  model: "#/model",
};

for (const [name, hash] of Object.entries(SCREENS)) {
  test(`a11y: ${name}`, async ({ page }) => {
    await serveData(page);
    await open(page, hash);
    const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const summary = result.violations.map((v) => `${v.id}: ${v.nodes.length}× ${v.help}`);
    expect(result.passes.length).toBeGreaterThan(10); // axe naozaj bežal
    expect(summary).toEqual([]);
  });
}

test("a11y: prepínač Čo keby je ovládateľný klávesnicou", async ({ page }) => {
  await serveData(page);
  await open(page, "#/cokeby/0022600001");
  const out = page.getByRole("button", { name: "NEHRÁ" });
  await out.focus();
  await page.keyboard.press("Enter");
  await expect(out).toHaveAttribute("aria-pressed", "true");
});
