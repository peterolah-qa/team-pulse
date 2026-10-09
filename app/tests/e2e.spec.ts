import { expect, test } from "@playwright/test";
import { fixture, open, serveData, withResults } from "./helpers";

test.beforeEach(async ({ page }) => {
  await serveData(page, { predictions: withResults });
});

const pcts = async (row: import("@playwright/test").Locator) =>
  (await row.locator(".tl .val").allTextContents()).map((t) => Number(t.replace(/\D/g, "")));

test("Zápasy: po dňoch v našom čase, tip a šance spolu presne 100 %", async ({ page }) => {
  await open(page);
  await expect(page.locator("h1")).toHaveText("Zápasy");
  await expect(page.locator(".tabbar a[aria-current=page]")).toHaveText("Zápasy");
  // zápasy z 20. 10. v USA začínajú u nás v stredu 21. 10. v noci → patria pod „Dnes“
  await expect(page.locator("h2.day > span:first-child")).toHaveText(["Dnes", "Zajtra", "Piatok 23. 10."]);
  await expect(page.locator("h2.day").first()).toContainText("streda 21. 10.");
  await expect(page.locator("section").first().locator("a.match")).toHaveCount(3);

  const first = page.locator("a.match").first();
  await expect(first.locator(".clock")).toHaveText("01:00");
  await expect(first.locator(".tl").first()).toContainText("BOS"); // hostia hore
  await expect(first.locator(".tl").nth(1)).toContainText("DETdoma");
  await expect(first.locator(".tl.fav")).toContainText("DET");
  await expect(first.locator(".tl.fav .tip")).toHaveText("tip");
  expect(await pcts(first)).toEqual([38, 62]);
  await expect(first.locator(".note")).toHaveText("BOS: bez I. Varga (?)");

  for (const row of await page.locator("a.match").all()) {
    const [a, h] = await pcts(row);
    expect(a + h).toBe(100);
    await expect(row.locator(".tl.fav")).toHaveCount(1);
  }
});

test("Zápasy: tip pri presne 50 % je na hostí, rovnako ako vo vyhodnotení modelu", async ({ page }) => {
  await page.unrouteAll();
  await serveData(page, {
    predictions: (p) => {
      p.days["2026-10-20"][2].p_home = 0.5;
      return p;
    },
  });
  await open(page);
  const row = page.locator("a.match", { hasText: "OKC" });
  expect(await pcts(row)).toEqual([50, 50]);
  await expect(row.locator(".tl.fav")).toContainText("OKC");
});

test("Zápasy: začatý zápas je „hrá sa“, dohraný už nie je medzi zápasmi", async ({ page }) => {
  await page.unrouteAll();
  await serveData(page, {
    predictions: (p) => {
      withResults(p);
      p.results.push({ ...p.results[1], game_id: "0022600002", home: "NYK", away: "PHI", tipoff_utc: "2026-10-21 00:00:00+00:00" });
      return p;
    },
  });
  await open(page, "#/", new Date("2026-10-21T01:20:00+02:00"));
  await expect(page.locator("a.match", { hasText: "PHI" }).first()).not.toContainText("02:00"); // PHI @ NYK je vo Výsledkoch
  await expect(page.locator("a.match").first().locator(".tag.live")).toHaveText("hrá sa"); // BOS @ DET od 01:00
  await expect(page.locator("a.match").nth(1).locator(".tag.live")).toHaveCount(0);
});

test("Tipy: favoriti od najväčšej šance, spolu = súčin šancí", async ({ page }) => {
  await open(page, "#/tipy");
  await expect(page.locator(".tabbar a[aria-current=page]")).toHaveText("Tipy");
  const rows = page.locator("a.tiprow");
  await expect(rows).toHaveCount(6);
  await expect(rows.locator(".rank")).toHaveText(["1", "2", "3", "4", "5", "6"]);
  await expect(rows.locator(".abbr")).toHaveText(["NYK", "DEN", "NYK", "DET", "DET", "SAS"]);
  await expect(rows.locator(".tipp")).toHaveText(["84 %", "73 %", "70 %", "62 %", "56 %", "54 %"]);
  await expect(rows.locator(".acc")).toHaveText([
    "najistejší tip",
    "tipy 1 – 2 spolu: 61 %",
    "tipy 1 – 3 spolu: 43 %",
    "tipy 1 – 4 spolu: 26 %",
    "tipy 1 – 5 spolu: 15 %",
    "tipy 1 – 6 spolu: 8 %",
  ]);
  await expect(rows.nth(0)).toContainText("doma s PHI");
  await expect(rows.nth(2)).toContainText("@ BOS");
  // percento tipu je rovnaké ako pri zápase v zozname Zápasy
  await rows.nth(1).click();
  await expect(page).toHaveURL(/#\/zapas\/0022600004$/);
  await expect(page.locator(".hero .side.fav .pct")).toHaveText("73 %");
});

test("Tipy: zápas, ktorý už začal, medzi tipmi nie je", async ({ page }) => {
  await open(page, "#/tipy", new Date("2026-10-21T01:20:00+02:00"));
  await expect(page.locator("a.tiprow")).toHaveCount(5);
  await expect(page.locator("a.tiprow", { hasText: "BOS" })).toHaveCount(1); // NYK @ BOS áno, BOS @ DET (01:00) nie
  await expect(page.locator("a.tiprow").nth(3)).toContainText("DET");
  await expect(page.locator("a.tiprow").nth(3)).toContainText("@ PHI");
});

test("Výsledky: po dňoch, súhrn tipov a nevyšiel = celý červený", async ({ page }) => {
  await open(page, "#/vysledky");
  await expect(page.locator(".tabbar a[aria-current=page]")).toHaveText("Výsledky");
  await expect(page.locator(".sub")).toHaveText("tipy vyšli v 1 z 2 zápasov");
  await expect(page.locator("h2.day > span:first-child")).toHaveText(["Včera", "Sobota 17. 10."]);
  const rows = page.locator("a.match");
  await expect(rows).toHaveCount(3);
  // najnovší hore: PHI @ NYK (02:00), potom BOS @ DET (01:00)
  await expect(rows.nth(0)).toHaveClass(/miss/);
  await expect(rows.nth(0).locator(".tipline")).toHaveText("Tip NYK 70 % · nevyšiel");
  await expect(rows.nth(0).locator(".tl.won")).toContainText("PHI104");
  await expect(rows.nth(1)).toHaveClass(/hit/);
  await expect(rows.nth(1).locator(".tipline")).toHaveText("Tip DET 62 % · vyšiel");
  await expect(rows.nth(2)).toHaveClass(/none/);
  await expect(rows.nth(2)).toContainText("príprava");
  await expect(rows.nth(2).locator(".tipline")).toHaveText("Tip pred zápasom sa neuložil");
  const red = await rows.nth(0).evaluate((el) => getComputedStyle(el).backgroundColor);
  const normal = await rows.nth(1).evaluate((el) => getComputedStyle(el).backgroundColor);
  expect(red).not.toBe(normal);
});

test("Výsledok: skóre, tip a štatistiky hráčov (MIN, B, D, A, BL)", async ({ page }) => {
  await open(page, "#/vysledky");
  await page.locator("a.match").nth(1).click();
  await expect(page).toHaveURL(/#\/vysledok\/0022600900$/);
  await expect(page.locator("h1")).toHaveText("BOS @ DET");
  await expect(page.locator(".sub")).toHaveText("utorok 20. 10., 01:00");
  await expect(page.locator(".score .side").nth(0)).toContainText("104");
  await expect(page.locator(".score .side.won")).toContainText("DETdoma110");
  await expect(page.locator(".score .verdict")).toContainText("DET 62 % · vyšiel");
  await expect(page.locator("h2.sec")).toHaveText(["Boston Celtics", "Detroit Pistons víťaz"]); // hostia, potom domáci
  const det = page.locator("h2.sec:has-text('Detroit Pistons') + section table.box").first();
  await expect(det.locator("thead th")).toHaveText(["Hráč", "MIN", "B", "D", "A", "BL"]);
  await expect(det.locator("tbody tr")).toHaveCount(8);
  await expect(det.locator("tbody tr").first().locator("td")).toHaveText(["Cade Cunningham", "36", "31", "7", "5", "1"]);
  const more = page.locator("details.more", { hasText: "Ďalší hráči (3)" });
  await expect(more).not.toHaveAttribute("open");
  await more.locator("summary").click();
  await expect(more.locator("tbody tr")).toHaveCount(3);
  await page.locator("a.back").click();
  await expect(page).toHaveURL(/#\/vysledky$/);
});

test("Detail zápasu: tip, prečo, otázny hráč, forma a podrobnosti modelu", async ({ page }) => {
  await open(page);
  await page.locator("a.match").first().click();
  await expect(page).toHaveURL(/#\/zapas\/0022600001$/);
  await expect(page.locator("h1")).toHaveText("BOS @ DET");
  await expect(page.locator(".sub")).toHaveText("streda 21. 10., 01:00");
  await expect(page.locator(".hero .side.fav")).toContainText("DET");
  await expect(page.locator(".hero .side.fav .pct")).toHaveText("62 %");
  await expect(page.locator(".hero .verdict")).toContainText("Tip: DET vyhrá so šancou 62 %");
  await expect(page.locator("ul.rows li").first()).toContainText(/DET Sila súpisky|BOS Bez I\. Varga/);
  await expect(page.locator("ul.rows").first().locator("li")).toHaveCount(2);
  const g = fixture("predictions").days["2026-10-20"][0];
  const out = Math.round(g.what_if[0].out.p_home * 100);
  await expect(page.locator("h2.sec", { hasText: "Otázni hráči" })).toBeVisible();
  await expect(page.locator("ul.card.rows li")).toContainText(`Ak I. Varga (BOS) nenastúpiDET 62 % → ${out} %`);
  await expect(page.locator("a.formrow")).toHaveCount(2);
  const det = page.locator("details.more", { hasText: "Podrobnosti modelu" });
  await expect(det).not.toHaveAttribute("open");
  await det.locator("summary").click();
  await expect(det.locator("thead th")).toHaveText(["Vplyv v Elo bodoch", "BOS", "DET"]);

  await page.locator("a.formrow", { hasText: "DET" }).click();
  await expect(page).toHaveURL(/#\/team\/DET$/);
  await page.goBack();
  await expect(page).toHaveURL(/#\/zapas\/0022600001$/);
});

test("Team: forma, najbližšie zápasy s našou šancou, posledné zápasy, zranení navrchu súpisky", async ({ page }) => {
  await open(page, "#/team/PHI");
  await expect(page.locator("h1")).toHaveText("Philadelphia 76ers");
  await expect(page.locator(".teamhero")).toContainText("Pulse 34");
  await expect(page.locator(".teamhero")).toContainText("7. v lige podľa formy");
  const up = page.locator("h2.sec:has-text('Najbližšie zápasy') + section li");
  await expect(up).toHaveCount(2);
  await expect(up.first()).toContainText("@ NYK");
  await expect(up.first()).toContainText("šanca 16 %");
  await expect(up.nth(1)).toContainText("doma s DET");
  await expect(up.nth(1)).toContainText("šanca 44 %");
  const recent = page.locator("h2.sec:has-text('Posledné zápasy') + section li");
  await expect(recent.first()).toContainText("V");
  await expect(recent.first()).toContainText("@ NYK");
  await expect(recent.first()).toContainText("104 : 99");
  const costa = page.locator("table.box tbody tr").first();
  await expect(costa).toContainText("O. Costa");
  await expect(costa.locator(".chip")).toHaveText("nehrá");
  await up.first().locator("a").click();
  await expect(page).toHaveURL(/#\/zapas\/0022600002$/);
});

test("Teamy: skupiny podľa formy, poradie sedí s Pulse", async ({ page }) => {
  await open(page, "#/teamy");
  await expect(page.locator("h2.day > span:first-child")).toHaveText(["Silní", "Stabilní", "Oslabení", "Kritickí"]);
  const rows = page.locator("a.teamrow");
  await expect(rows).toHaveCount(8);
  await expect(rows.locator(".rank")).toHaveText(["1", "2", "3", "4", "5", "6", "7", "8"]);
  await expect(rows.locator(".abbr")).toHaveText(["NYK", "OKC", "SAS", "DET", "DEN", "BOS", "PHI", "LAL"]);
  const pulses = (await rows.locator(".pulse").allTextContents()).map(Number);
  expect([...pulses].sort((a, b) => b - a)).toEqual(pulses);
  await rows.nth(1).click();
  await expect(page).toHaveURL(/#\/team\/OKC$/);
});

test("Model: presnosť, kalibrácia, podrobnosti po rozkliknutí", async ({ page }) => {
  await open(page, "#/model");
  await expect(page.locator(".big-n")).toHaveText("67,3 %");
  await expect(page.locator("svg.cal")).toBeVisible();
  const more = page.locator("details.more");
  await more.locator("summary").click();
  await expect(more.locator("tr.best")).toHaveCount(1);
  await expect(more.locator("li", { hasText: "Hostia: 2. zápas za 2 dni" })).toContainText("−");
});

test("appka nikde neukazuje kurzy ani odkazy na stávkové kancelárie", async ({ page }) => {
  for (const hash of ["#/", "#/tipy", "#/vysledky", "#/vysledok/0022600900", "#/zapas/0022600001", "#/team/PHI", "#/teamy", "#/model"]) {
    await open(page, hash);
    await expect(page.locator("body")).not.toContainText(/kurz|odds|vsaď|tipsport|fortuna|nike\.sk/i);
  }
});

test("prázdne stavy: žiadne zápasy, žiadne výsledky", async ({ page }) => {
  await page.unrouteAll();
  await serveData(page, { predictions: (p) => ({ ...p, days: {}, results: [] }) });
  await open(page);
  await expect(page.locator(".empty")).toContainText("Žiadne naplánované zápasy");
  await page.locator(".tabbar a", { hasText: "Tipy" }).click();
  await expect(page.locator(".empty")).toContainText("Žiadne zápasy, ktoré ešte nezačali");
  await page.locator(".tabbar a", { hasText: "Výsledky" }).click();
  await expect(page.locator(".empty")).toContainText("Zatiaľ žiadne dohrané zápasy");
});

test("neznámy zápas, výsledok a team", async ({ page }) => {
  await open(page, "#/zapas/nic");
  await expect(page.locator("h1")).toHaveText("Zápas sa nenašiel");
  await open(page, "#/vysledok/nic");
  await expect(page.locator("h1")).toHaveText("Výsledok sa nenašiel");
  await open(page, "#/team/XYZ");
  await expect(page.locator("h1")).toHaveText("Team sa nenašiel");
});

test("staré odkazy na Čo keby vedú na detail zápasu", async ({ page }) => {
  await open(page, "#/cokeby/0022600001");
  await expect(page.locator("h1")).toHaveText("BOS @ DET");
  await expect(page.locator(".tabbar a")).toHaveText(["Zápasy", "Tipy", "Výsledky", "Teamy", "Model"]);
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
  await expect(page.locator("a.match")).toHaveCount(6);
});

test("žiadna obrazovka sa neposúva do strán", async ({ page }, info) => {
  if (info.project.name === "mobile") await page.setViewportSize({ width: 360, height: 780 }); // malý Android
  for (const hash of ["#/", "#/tipy", "#/vysledky", "#/vysledok/0022600900", "#/zapas/0022600001", "#/team/PHI", "#/teamy", "#/model"]) {
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
