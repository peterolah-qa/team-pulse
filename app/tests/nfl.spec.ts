import { expect, test } from "@playwright/test";
import { fixture, listMode, nflReady, open, serveData } from "./helpers";

/* NFL (beta): prepínač, zápasy, tipy, výsledky, detail s rozpadom tipu, tímy a model. Dáta = skutočný výstup
   team_pulse.nfl.app_data z 28. 10. 2026 (týždeň 8). „Teraz“ = streda 21. 10. 0:30, všetky zápasy sú v budúcnosti. */
test.beforeEach(async ({ page }) => {
  await listMode(page);
  await serveData(page);
});

const nfl = async (page: import("@playwright/test").Page, hash = "#/nfl/") => {
  await open(page, hash);
  await nflReady(page);
};

test("prepínač: NBA → NFL na tej istej záložke, beta pri NFL, záložky vedú do NFL", async ({ page }) => {
  await open(page, "#/tipy");
  const sw = page.getByRole("navigation", { name: "Šport" });
  await expect(sw.getByRole("link", { name: /NFL/ })).toContainText("beta");
  await sw.getByRole("link", { name: /NFL/ }).click();
  await expect(page).toHaveURL(/#\/nfl\/tipy$/);
  await nflReady(page);
  await expect(page).toHaveTitle("NFL · Tipy · Team Pulse");
  expect(await page.locator(".tabbar a").evaluateAll((as) => as.map((a) => a.getAttribute("href")))).toEqual([
    "#/nfl/", "#/nfl/tipy", "#/nfl/vysledky", "#/nfl/teamy", "#/nfl/model",
  ]);
});

test("Zápasy NFL: všetkých 14 zápasov týždňa 8 so šancou podľa zamknutého tipu", async ({ page }) => {
  await nfl(page);
  const data = fixture("nfl/predictions");
  const all = Object.values(data.days).flat() as { game_id: string; p_home: number }[];
  await expect(page.locator("a.match")).toHaveCount(all.length);
  const gb = page.locator('a.match[href="#/nfl/zapas/2026_08_CAR_GB"]');
  await expect(gb).toContainText("GB");
  await expect(gb).toContainText("66 %");
  await expect(gb).toContainText("34 %");
  await expect(gb).toContainText("QB Bryce Young – Jordan Love");
  await expect(page.locator(".beta-note")).toContainText("ostré meranie beží do 10. 1. 2027");
});

test("Detail NFL: rozpad tipu sa sčíta na zamknutú šancu a je overený prepočtom", async ({ page }) => {
  await nfl(page, "#/nfl/zapas/2026_08_CAR_GB");
  await expect(page.locator("h1")).toHaveText("CAR @ GB");
  const edge = page.locator(".card.edge");
  await expect(edge.locator(".erow")).toHaveCount(2);
  await expect(edge.locator(".erow").nth(0)).toContainText("+66,7");
  await expect(edge.locator(".erow").nth(1)).toContainText("+48,0");
  await expect(edge.locator(".etotal")).toContainText("+114,7 Elo → 66 %");
  await expect(edge.locator(".okchip")).toContainText("Prepočítané");
  await expect(page.getByRole("heading", { name: "Quarterbacky" })).toBeVisible();
  await expect(page.locator(".trend2 .trow")).toHaveCount(2);
});

test("Tipy NFL: favoriti od najväčšej šance, prvý TEN @ CIN → CIN 84 %", async ({ page }) => {
  await nfl(page, "#/nfl/tipy");
  await expect(page.locator("a.tiprow").first()).toContainText("CIN");
  await expect(page.locator("a.tiprow").first()).toContainText("84 %");
  await expect(page.locator("a.tiprow")).toHaveCount(14);
});

test("Výsledky NFL: posledný týždeň bez tipu (pred ostrým meraním)", async ({ page }) => {
  await nfl(page, "#/nfl/vysledky");
  await expect(page.locator(".match.result")).toHaveCount(fixture("nfl/predictions").results.length);
  await expect(page.locator(".match.result").first()).toContainText("Pred ostrým meraním");
});

test("Teamy a Model NFL: 32 tímov podľa Ela, test 2023 – 2025 a ostré meranie oboch modelov", async ({ page }) => {
  await nfl(page, "#/nfl/teamy");
  await expect(page.locator(".teamrow")).toHaveCount(32);
  await expect(page.locator(".teamrow").first()).toContainText("SEA");
  await nfl(page, "#/nfl/model");
  await expect(page.locator(".big-n")).toHaveText("63,9 %");
  await expect(page.getByText("Elo + quarterback (nfl-elo-qb-v1)")).toBeVisible();
  await expect(page.getByText(/Elo: ostré meranie/)).toBeVisible();
});

test("chýbajúce NFL dáta: chybová hláška s tlačidlom, NBA funguje ďalej", async ({ page }) => {
  await page.route(/\/nfl\/predictions\.json$/, (r) => r.fulfill({ status: 404, body: "" }));
  await open(page, "#/nfl/");
  await expect(page.getByRole("alert")).toContainText("NFL dáta sa nepodarilo načítať");
  await open(page, "#/");
  await expect(page.locator("a.match")).toHaveCount(6);
});
