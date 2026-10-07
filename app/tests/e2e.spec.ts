import { expect, test } from "@playwright/test";
import { fixture, open, serveData, withResults } from "./helpers";

test.beforeEach(async ({ page }) => {
  await serveData(page);
});

test("Dnes: zápasy po dňoch, úrovne a šance", async ({ page }) => {
  await open(page);
  await expect(page.locator("h1")).toHaveText("DNES");
  await expect(page.locator("article.game")).toHaveCount(6);
  await expect(page.locator("h2.section")).toHaveCount(3);
  const first = page.locator("article.game").first();
  await expect(first).toContainText("DET");
  await expect(first).toContainText("OSLABENÝ");
  await expect(first).toContainText("62 %");
  await expect(first).toContainText("I. Varga otázny");
  await expect(page.locator(".tabbar a[aria-current=page]")).toHaveText("Dnes");
});

test("Pulse sa zobrazuje nadol, aby sedel s úrovňou (49,5 → 49 Oslabený)", async ({ page }) => {
  await open(page);
  await expect(page.locator("article.game").first().locator(".pulse-num").first()).toHaveText("49");
});

test("appka nikde neukazuje kurzy ani odkazy na stávkové kancelárie", async ({ page }) => {
  for (const hash of ["#/", "#/zapas/0022600001", "#/team/PHI", "#/cokeby", "#/model"]) {
    await open(page, hash);
    await expect(page.locator("body")).not.toContainText(/kurz|odds|vsaď|tipsport|fortuna|nike\.sk/i);
  }
});

test("Dnes → Zápas → Team → späť", async ({ page }) => {
  await open(page);
  await page.locator("article.game").first().locator("a.stretch").click();
  await expect(page).toHaveURL(/#\/zapas\/0022600001$/);
  await expect(page.locator("h1")).toContainText("DET");
  await expect(page.locator("h1")).toContainText("BOS");
  await expect(page.locator(".layer")).toHaveCount(5);
  await expect(page.locator(".reason")).toContainText(["DET: Sila súpisky", "BOS: Bez I. Varga (?)"]);

  await page.locator("h1 a", { hasText: "DET" }).click();
  await expect(page).toHaveURL(/#\/team\/DET$/);
  await expect(page.locator("h1")).toHaveText(/Detroit Pistons/i);
  await expect(page.locator("svg.spark")).toBeVisible();
  await expect(page.locator(".tabbar a[aria-current=page]")).toHaveText("Teamy");

  await page.goBack();
  await expect(page).toHaveURL(/#\/zapas\/0022600001$/);
});

test("Team: zranený hráč OUT so zápornou hodnotou a najbližšie zápasy", async ({ page }) => {
  await open(page, "#/team/PHI");
  const costa = page.locator(".reason", { hasText: "O. Costa" }).last();
  await expect(costa).toContainText("OUT");
  await expect(costa).toContainText("−32");
  await page.locator("a.reason.link").first().click();
  await expect(page).toHaveURL(/#\/zapas\//);
});

test("Teamy: mriežka zoradená podľa poradia", async ({ page }) => {
  await open(page, "#/teamy");
  const tiles = page.locator("a.tile");
  await expect(tiles).toHaveCount(8);
  await expect(tiles.first()).toContainText("NYK");
  await tiles.nth(1).click();
  await expect(page).toHaveURL(/#\/team\/OKC$/);
});

test("Čo keby: prepínač HRÁ / NEHRÁ zmení Pulse a šancu", async ({ page }) => {
  await open(page, "#/zapas/0022600001");
  await page.getByRole("link", { name: /Čo keby: I. Varga/ }).click();
  await expect(page).toHaveURL(/#\/cokeby\/0022600001$/);
  const card = page.locator(".whatif");
  await expect(card).toHaveCount(1);
  await expect(card.locator(".ring-num")).toHaveText("44");
  await expect(card.locator(".phome")).toHaveText("60 %");

  await card.getByRole("button", { name: "NEHRÁ" }).click();
  await expect(card.getByRole("button", { name: "NEHRÁ" })).toHaveAttribute("aria-pressed", "true");
  await expect(card.getByRole("button", { name: "HRÁ", exact: true })).toHaveAttribute("aria-pressed", "false");
  await expect(card.locator(".ring-num")).toHaveText("40");
  await expect(card.locator(".phome")).toHaveText("63 %");

  await card.getByRole("button", { name: "HRÁ", exact: true }).click();
  await expect(card.locator(".ring-num")).toHaveText("44");
});

test("Čo keby: všetci otázni hráči a varovanie pri hraničnom prípade", async ({ page }) => {
  await page.unrouteAll();
  await serveData(page, {
    predictions: (p) => {
      p.days["2026-10-20"][0].what_if[0].out.tier = "Kritický";
      return p;
    },
  });
  await open(page, "#/cokeby");
  await expect(page.locator(".whatif")).toHaveCount(3);
  await expect(page.locator(".whatif").first().locator(".warn")).toContainText("HRANIČNÝ PRÍPAD");
  await expect(page.locator(".whatif").nth(1).locator(".warn")).toHaveCount(0);
});

test("Model: presnosť, kalibrácia a vrstvy", async ({ page }) => {
  await open(page, "#/model");
  const m = fixture("model");
  await expect(page.locator(".big")).toHaveText(/67,3 %/);
  await expect(page.locator("svg.cal")).toBeVisible();
  await expect(page.locator("table").first().locator("tbody tr")).toHaveCount(m.calibration.length);
  await expect(page.locator("tr.best")).toHaveCount(1);
  await expect(page.locator(".reason", { hasText: "Hostia: 2. zápas za 2 dni" })).toContainText("−");
});

test("prázdny deň: žiadne zápasy ani otázni hráči", async ({ page }) => {
  await page.unrouteAll();
  await serveData(page, { predictions: (p) => ({ ...p, days: {} }) });
  await open(page);
  await expect(page.locator(".empty")).toContainText("Žiadne naplánované zápasy");
  await page.locator(".tabbar a", { hasText: "Čo keby" }).click();
  await expect(page.locator(".empty")).toContainText("Žiadni otázni hráči");
});

test("neznámy zápas a team", async ({ page }) => {
  await open(page, "#/zapas/nic");
  await expect(page.locator(".empty")).toContainText("Zápas sa nenašiel");
  await open(page, "#/team/XYZ");
  await expect(page.locator(".empty")).toContainText("Team sa nenašiel");
});

test("výpadok dát: chyba a tlačidlo Skúsiť znova", async ({ page }) => {
  await page.unrouteAll();
  let fail = true;
  await page.route("**/data/*.json", async (route) => {
    if (fail) return route.fulfill({ status: 503, body: "down" });
    const name = route.request().url().split("/").pop()!.replace(".json", "") as "predictions";
    return route.fulfill({ json: fixture(name) });
  });
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("Dáta sa nepodarilo načítať");
  fail = false;
  await page.getByRole("button", { name: "Skúsiť znova" }).click();
  await expect(page.locator("article.game")).toHaveCount(6);
});

test("žiadna obrazovka sa neposúva do strán", async ({ page }, info) => {
  if (info.project.name === "mobile") await page.setViewportSize({ width: 360, height: 780 }); // malý Android
  for (const hash of ["#/", "#/zapas/0022600001", "#/team/PHI", "#/teamy", "#/cokeby", "#/model"]) {
    await open(page, hash);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, hash).toBeLessThanOrEqual(0);
  }
});

test("PWA: manifest a ikony sú dostupné", async ({ page, request }) => {
  await open(page);
  const href = await page.locator("link[rel=manifest]").getAttribute("href");
  const manifest = await (await request.get(`/${href}`)).json();
  expect(manifest.display).toBe("standalone");
  for (const icon of manifest.icons) expect((await request.get(`/${icon.src}`)).ok(), icon.src).toBeTruthy();
  expect((await request.get("/sw.js")).ok()).toBeTruthy();
});

test("príprava: štítok na karte, poznámka v detaile a v najbližších zápasoch teamu", async ({ page }) => {
  await page.unrouteAll();
  const first = (p: any) => Object.values(p.days as Record<string, any[]>).find((g) => g.length)![0];
  let abbr = "";
  await serveData(page, {
    predictions: (p) => {
      first(p).kind = "preseason";
      return p;
    },
    teams: (t) => {
      [abbr] = Object.entries(t.teams as Record<string, any>).find(([, x]) => x.upcoming.length)!;
      t.teams[abbr].upcoming[0].kind = "preseason";
      return t;
    },
  });
  await open(page);
  const card = page.locator("article.game").first();
  await expect(card).toContainText("PRÍPRAVA");
  await expect(page.locator("article.game").nth(1)).not.toContainText("PRÍPRAVA");
  await card.locator("a.stretch").click();
  await expect(page.locator(".pre-note")).toContainText("do vyhodnotenia sa neráta");
  await open(page, `#/team/${abbr}`);
  await expect(page.locator("a.reason.link").first()).toContainText("príprava");
});

test("výsledky: skóre, náš tip a štatistiky hráčov podľa súpisky", async ({ page }) => {
  await page.unrouteAll();
  await serveData(page, { predictions: withResults });
  await open(page);
  const cards = page.locator("article.result");
  await expect(cards).toHaveCount(2);
  await expect(cards.first()).toContainText("tip DET 62 %");
  await expect(cards.first().locator(".hit")).toHaveText("✓");
  await expect(cards.nth(1)).toContainText("PRÍPRAVA");
  await expect(cards.nth(1)).toContainText("tip neuložený");

  await cards.first().locator("a.stretch").click();
  await expect(page.locator("h1")).toContainText("110 : 104");
  await expect(page.locator(".note")).toContainText("✓ trafený");
  const det = page.locator("table.box").first();
  await expect(det.locator("thead")).toContainText("MIN");
  await expect(det.locator("tbody tr").first()).toContainText("Cade Cunningham");
  await expect(det.locator("tbody tr").first().locator("td")).toHaveText(["Cade Cunningham", "36", "31", "7", "5", "1", "2"]);
  const width = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(width).toBeLessThanOrEqual(0);

  await open(page, "#/vysledok/0012600050");
  await expect(page.locator(".empty")).toContainText("Štatistiky hráčov zatiaľ nie sú");
  await open(page, "#/vysledok/neznamy");
  await expect(page.locator(".empty")).toContainText("Výsledok sa nenašiel");
});
