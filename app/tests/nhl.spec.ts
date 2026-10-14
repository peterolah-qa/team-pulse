import { expect, test } from "@playwright/test";
import { fixture, isData, open, serveData, withResults } from "./helpers";

/* NHL (beta): prepínač športu, zápasy, tipy, výsledky, detail, teamy a model. „Teraz“ = streda 21. 10. 0:30. */
test.beforeEach(async ({ page }) => {
  await serveData(page, { predictions: withResults });
});

const nhl = async (page: import("@playwright/test").Page, hash = "#/nhl/") => {
  await open(page, hash);
  await page.locator(".beta-note").first().waitFor();
};

const pcts = async (row: import("@playwright/test").Locator) =>
  (await row.locator(".tl .val").allTextContents()).map((t) => Number(t.replace(/\D/g, "")));

test("prepínač: NBA → NHL na tej istej záložke, záložky vedú do NHL, späť na NBA", async ({ page }) => {
  await open(page, "#/tipy");
  const sw = page.getByRole("navigation", { name: "Šport" });
  await expect(sw.locator("a[aria-current=page]")).toHaveText("NBA");
  await sw.getByRole("link", { name: /NHL/ }).click();
  await expect(page).toHaveURL(/#\/nhl\/tipy$/);
  await page.locator(".beta-note").first().waitFor();
  await expect(page.getByRole("navigation", { name: "Šport" }).locator("a[aria-current=page]")).toContainText("NHL");
  await expect(page.locator(".tabbar a")).toHaveText(["Zápasy", "Tipy", "Výsledky", "Teamy", "Model"]);
  await expect(page.locator(".tabbar a[aria-current=page]")).toHaveText("Tipy");
  expect(await page.locator(".tabbar a").evaluateAll((as) => as.map((a) => a.getAttribute("href")))).toEqual([
    "#/nhl/", "#/nhl/tipy", "#/nhl/vysledky", "#/nhl/teamy", "#/nhl/model",
  ]);
  await expect(page).toHaveTitle("NHL · Tipy · Team Pulse");
  await page.getByRole("navigation", { name: "Šport" }).getByRole("link", { name: "NBA" }).click();
  await expect(page).toHaveURL(/#\/tipy$/);
  await expect(page.locator("a.tiprow")).toHaveCount(6);
});

test("nainštalovaná appka sa otvorí v naposledy zvolenom športe, odkaz na #/ ostáva NBA", async ({ page }) => {
  await nhl(page);
  await page.goto("/");
  await page.locator(".beta-note").first().waitFor();
  await expect(page).toHaveURL(/#\/nhl\/$/);
  await open(page, "#/");
  await expect(page.locator(".beta-note")).toHaveCount(0);
  await expect(page.locator("a.match")).toHaveCount(6);
});

test("Zápasy NHL: po dňoch v našom čase, tip, šance spolu 100 %, únava v poznámke, klzisko v pozadí", async ({ page }) => {
  await nhl(page);
  await expect(page.locator("h2.day > span:first-child")).toHaveText(["Dnes", "Zajtra"]);
  const rows = page.locator("a.match");
  await expect(rows).toHaveCount(4);
  const first = rows.first();
  await expect(first.locator(".clock")).toHaveText("01:00");
  await expect(first.locator(".tl.fav")).toContainText("BUF");
  expect(await pcts(first)).toEqual([54, 46]);
  await expect(rows.nth(1).locator(".note")).toHaveText("DAL: back-to-back · COL: back-to-back");
  for (const row of await rows.all()) {
    const [a, h] = await pcts(row);
    expect(a + h).toBe(100);
    await expect(row.locator(".mbar")).toHaveCount(1);
  }
  await expect(rows.last().locator(".tl.fav")).toContainText("SEA"); // presne 50 % = tip na hostí
  await expect(page.locator(".court.rink")).toBeVisible();
  await expect(page.locator(".court.hoops")).toBeHidden();
});

test("Tipy NHL: od najväčšej šance, spolu = súčin, graf, detail z tipu", async ({ page }) => {
  await nhl(page, "#/nhl/tipy");
  const rows = page.locator("a.tiprow");
  await expect(rows.locator(".abbr")).toHaveText(["FLA", "COL", "BUF", "SEA"]);
  await expect(rows.locator(".tipp")).toHaveText(["66 %", "60 %", "54 %", "50 %"]);
  await expect(rows.locator(".acc")).toHaveText(["najistejší tip", "tipy 1 – 2 spolu: 40 %", "tipy 1 – 3 spolu: 21 %", "tipy 1 – 4 spolu: 11 %"]);
  await expect(page.locator("svg.acc-chart")).toHaveAttribute("aria-label", /1 tip 66 %, 2 tipy 40 %, 3 tipy 21 %, 4 tipy 11 %/);
  await rows.nth(1).click();
  await expect(page).toHaveURL(/#\/nhl\/zapas\/2026020201$/);
  await expect(page.locator(".hero .side.fav .pct")).toHaveText("60 %");
});

test("Výsledky NHL: včera a dnes, pp a sn, nevyšiel červený, bez tipu", async ({ page }) => {
  await nhl(page, "#/nhl/vysledky");
  await expect(page.locator(".sub")).toHaveText("tipy vyšli v 1 z 2 zápasov");
  const rows = page.locator(".match.result");
  await expect(rows).toHaveCount(3); // CAR – PIT zo 17. 10. je starší
  await expect(rows.nth(0)).toContainText("sn");
  await expect(rows.nth(0)).toContainText("Tip pred zápasom sa neuložil");
  await expect(rows.nth(1)).toHaveClass(/miss/);
  await expect(rows.nth(1).locator(".tipline")).toHaveText("Tip BOS 55 % · nevyšiel");
  await expect(rows.nth(2)).toHaveClass(/hit/);
  await expect(rows.nth(2)).toContainText("pp");
});

test("Detail zápasu NHL: tip, prečo (Elo, domáce prostredie, únava), čas zamknutia", async ({ page }) => {
  await nhl(page, "#/nhl/zapas/2026020201");
  await expect(page.locator("h1")).toHaveText("DAL @ COL");
  await expect(page.locator(".tname")).toHaveText(["Dallas Stars", "Colorado Avalanche"]);
  await expect(page.locator(".verdict")).toContainText("Tip: COL vyhrá so šancou 60 %");
  const why = page.locator(".rows li");
  await expect(why.nth(0)).toContainText("COL silnejší (Elo 1582 : 1541)");
  await expect(why.nth(1)).toContainText("COL domáce prostredie");
  await expect(why.filter({ hasText: "3. zápas za 4 dni" })).toContainText("oslabuje −16");
  await expect(page.locator(".meta")).toContainText("Tip zamknutý");
  await open(page, "#/nhl/zapas/nic");
  await expect(page.locator("h1")).toHaveText("Zápas sa nenašiel");
});

test("Detail zápasu NHL: chýbajúci hráči z ESPN, bez vplyvu na tip", async ({ page }) => {
  await nhl(page, "#/nhl/zapas/2026020201");
  const card = page.locator("section.card", { has: page.locator("li", { hasText: "Seguin" }) });
  const rows = card.locator(".rows li");
  await expect(rows).toHaveCount(3);
  await expect(rows.nth(0)).toContainText("DAL Tyler Seguin dlhodobo");
  await expect(rows.nth(0)).toContainText("C · bedro");
  await expect(rows.nth(0)).toContainText("návrat asi 2. 11.");
  await expect(rows.nth(1)).toContainText("DAL Jason Robertson otázny");
  await expect(rows.nth(1)).not.toContainText("návrat");
  await expect(rows.nth(2)).toContainText("COL nikto nechýba");
  await expect(card).toContainText("Model NHL ich zatiaľ nepočíta, tip sa podľa nich nemení");
  await expect(page.locator(".verdict")).toContainText("Tip: COL vyhrá so šancou 60 %");
});

test("Detail zápasu NHL: zranenia sa nestiahli → sekcia chýbajúcich hráčov nie je", async ({ page }) => {
  await serveData(page, { "nhl/predictions": (j) => ({ ...j, injuries: null }) });
  await nhl(page, "#/nhl/zapas/2026020201");
  await expect(page.locator("h2", { hasText: "Prečo" })).toBeVisible();
  await expect(page.locator("h2", { hasText: "Chýbajúci hráči" })).toHaveCount(0);
});

test("Teamy NHL: poradie podľa Ela, Model NHL: presnosť a vrstvy", async ({ page }) => {
  await nhl(page, "#/nhl/teamy");
  const rows = page.locator(".teamrow");
  await expect(rows).toHaveCount(8);
  const elos = (await rows.locator(".pulse").allTextContents()).map(Number);
  expect([...elos].sort((a, b) => b - a)).toEqual(elos);
  await expect(rows.first()).toContainText("Colorado Avalanche");
  await expect(rows.locator("a")).toHaveCount(0); // bez detailu teamu

  await nhl(page, "#/nhl/model");
  await expect(page.locator(".big-n")).toHaveText("57,6 %");
  await expect(page.locator(".hero")).toContainText("54,3 %");
  await page.locator("details.more summary").click();
  await expect(page.locator("details.more li", { hasText: "Hostia: 2. zápas za 2 dni" })).toContainText("−");
});

test("NHL dáta chýbajú: chyba, NBA funguje ďalej, Skúsiť znova", async ({ page }) => {
  await page.unrouteAll();
  let down = true;
  await page.route(isData, async (route) => {
    const name = route.request().url().split("/data/").pop()!.replace(".json", "") as "predictions";
    if (down && name.startsWith("nhl/")) return route.fulfill({ status: 404, body: "nie je" });
    return route.fulfill({ json: name === "predictions" ? withResults(fixture(name)) : fixture(name) });
  });
  await open(page, "#/nhl/");
  await expect(page.getByRole("alert")).toContainText("NHL dáta sa nepodarilo načítať");
  await page.getByRole("navigation", { name: "Šport" }).getByRole("link", { name: "NBA" }).click();
  await expect(page.locator("a.match")).toHaveCount(6);
  await page.goBack();
  down = false;
  await page.getByRole("button", { name: "Skúsiť znova" }).click();
  await expect(page.locator("a.match")).toHaveCount(4);
});

test("NHL: žiadne kurzy, žiadne posúvanie do strán", async ({ page }, info) => {
  if (info.project.name === "mobile") await page.setViewportSize({ width: 360, height: 780 });
  for (const hash of ["#/nhl/", "#/nhl/tipy", "#/nhl/vysledky", "#/nhl/zapas/2026020201", "#/nhl/teamy", "#/nhl/model"]) {
    await nhl(page, hash);
    await expect(page.locator("body")).not.toContainText(/kurz|odds|vsaď|tipsport|fortuna|nike\.sk/i);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, hash).toBeLessThanOrEqual(0);
  }
});
