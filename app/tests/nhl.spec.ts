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

test("Zápasy NHL: po dňoch v našom čase, tip, šance spolu 100 %, únava v poznámke", async ({ page }) => {
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
  await expect(page.locator(".hero2 .pnum.fav")).toHaveText("60 %");
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

const nums = (texts: string[]) => texts.map((t) => Number(t.replace("−", "-").replace(",", ".").replace(/[^\d.+-]/g, "")));

test("Detail zápasu NHL: hlavička, šance, tip, aréna, bilancia, forma, odpočinok", async ({ page }) => {
  await nhl(page, "#/nhl/zapas/2026020201");
  await expect(page.locator("h1")).toHaveText("DAL @ COL");
  const hero = page.locator(".hero2");
  await expect(hero.locator(".hmeta")).toContainText("Dnes 03:00");
  await expect(hero.locator(".hmeta")).toContainText("Ball Arena");
  await expect(hero.locator(".tfull")).toHaveText(["Dallas Stars", "Colorado Avalanche"]);
  await expect(hero.locator(".pnum")).toHaveText(["40 %", "60 %"]);
  await expect(hero.locator(".pnum.fav")).toHaveText("60 %");
  await expect(hero.locator(".tipbox")).toContainText("COL vyhrá");
  await expect(hero.locator(".rec").first()).toContainText("3-2-1");
  await expect(hero.locator(".dots").first().locator(".dot5")).toHaveText(["V", "V", "P", "V", "P"]); // od najstaršieho
  await expect(hero.locator(".facts li").first()).toHaveText(/DAL\s*back-to-back · 3\. zápas za 4 dni/);
  await expect(hero.locator(".facts li").nth(1)).toHaveText(/COL\s*back-to-back · posun o 1 h na východ/);
  const rest = page.locator(".tcard", { hasText: "Naposledy" });
  await expect(rest.first()).toContainText("Naposledy včera doma s UTA, prehra po predĺžení alebo nájazdoch");
  await expect(rest.nth(1)).toContainText("Naposledy včera vonku u VGK, výhra");
  const form = page.locator(".tcard", { has: page.locator(".last5") });
  await expect(form.first()).toContainText("Doma 2-1-1");
  await expect(form.first()).toContainText("Vonku 1-1-0");
  await expect(form.first()).toContainText("Góly na zápas 3,17 : 2,83");
  await expect(form.first().locator(".last5 li").first()).toContainText("doma UTA");
  await expect(form.first().locator(".last5 li").first()).toContainText("2:3 pp");
  await expect(page.locator(".meta")).toContainText("Tip zamknutý");
  await open(page, "#/nhl/zapas/nic");
  await expect(page.locator("h1")).toHaveText("Zápas sa nenašiel");
});

test("Detail zápasu NHL: rozpad tipu v Elo bodoch sedí na zamknutú šancu", async ({ page }) => {
  await nhl(page, "#/nhl/zapas/2026020201");
  const edge = page.locator(".edge");
  await expect(page.locator("h2", { hasText: "Prečo 60 % pre COL" })).toBeVisible();
  await expect(edge.locator(".erow").first()).toContainText("Rozdiel v Elo");
  await expect(edge.locator(".erow").first()).toContainText("DAL 1541 : COL 1582");
  await expect(edge.locator(".erow", { hasText: "COL: back-to-back" }).locator(".ev")).toHaveText("−42,5");
  await expect(edge.locator(".erow", { hasText: "DAL: back-to-back" }).locator(".ev")).toHaveText("+38,5");
  await expect(edge.locator(".erow", { hasText: "Drobné vplyvy" }).locator(".ev")).toHaveText("+0,2"); // posun 1 h
  const values = nums(await edge.locator(".erow .ev").allTextContents());
  expect(values.reduce((a, b) => a + b, 0)).toBeCloseTo(74.1, 5);
  await expect(edge.locator(".etotal")).toContainText("+74,1 Elo → 60 %");
  await expect(edge.locator(".okchip")).toContainText("Prepočítané");
});

test("Detail zápasu NHL: favorit hostia – rozpad z pohľadu tipu, bez rozpisu", async ({ page }) => {
  await nhl(page, "#/nhl/zapas/2026020200");
  await expect(page.locator("h2", { hasText: "Prečo 54 % pre BUF" })).toBeVisible();
  const edge = page.locator(".edge");
  await expect(edge.locator(".erow").first().locator(".ev")).toHaveText("+59,5");
  await expect(edge.locator(".erow", { hasText: "TOR: domáci ľad" }).locator(".ev")).toHaveText("−20,0");
  await expect(edge.locator(".etotal")).toContainText("+26,1 Elo → 54 %");
  await expect(edge.locator(".okchip")).toHaveCount(0);
  await expect(edge).toContainText("Rozpis klubov nie je k dispozícii");
  await expect(page.locator(".trow").nth(1)).toContainText("zatiaľ 1 zápas s tipom");
  for (const h of ["Forma v sezóne", "Porovnanie", "Vzájomné zápasy"]) await expect(page.locator("h2", { hasText: h })).toHaveCount(0);
});

test("Detail zápasu NHL: porovnanie s poradím v lige a vzájomné zápasy", async ({ page }) => {
  await nhl(page, "#/nhl/zapas/2026020201");
  const rows = page.locator(".cmp .crow");
  await expect(rows).toHaveCount(6);
  await expect(rows.nth(0).locator(".c")).toHaveText("Góly na zápas");
  await expect(rows.nth(0).locator(".a")).toContainText("3,17");
  await expect(rows.nth(0).locator(".a .rk")).toHaveText("9."); // poradie v lige
  await expect(rows.nth(0).locator(".h")).toContainText("3,71");
  await expect(rows.nth(0).locator(".h .rk")).toHaveText("2.");
  await expect(rows.nth(0).locator(".h")).toHaveClass(/better/);
  await expect(rows.nth(2).locator(".h")).toContainText("29,6 %");
  await expect(rows.nth(3).locator(".a")).toHaveClass(/better/); // oslabenia: DAL 81,3 % > COL 78,3 %
  await expect(rows.nth(5).locator(".a")).toHaveClass(/better/); // strely súpera: menej je lepšie
  const h2h = page.locator(".h2h li");
  await expect(h2h).toHaveCount(3);
  await expect(h2h.first().locator(".sc")).toHaveText("COL 2:3 DAL");
  await expect(h2h.first()).toContainText("výhra DAL");
  await expect(h2h.first()).toContainText("po predĺžení");
  await expect(h2h.nth(1).locator(".sc")).toHaveText("DAL 1:4 COL");
});

test("Detail zápasu NHL: Sledovať zápas → po dohraní upozornenie a koniec sledovania", async ({ page }) => {
  await nhl(page, "#/nhl/zapas/2026020201");
  const btn = page.locator("#follow");
  await expect(btn).toHaveAttribute("aria-pressed", "false");
  await expect(btn).toBeInViewport(); // prichytené nad spodnou lištou
  await btn.click();
  await expect(page.locator("#follow")).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("#follow")).toHaveText("Sledujem zápas");
  await expect(page.locator("#toasts")).toContainText("Keď sa zápas dohrá");
  await page.reload();
  await expect(page.locator("#follow")).toHaveAttribute("aria-pressed", "true");
  // zápas sa dohral: COL vyhral 4:2 → tip vyšiel
  await page.unrouteAll();
  await serveData(page, {
    "nhl/predictions": (j) => ({
      ...j,
      results: [...j.results, { game_id: "2026020201", date: "2026-10-20", tipoff_utc: "2026-10-21T01:00:00Z", kind: "regular",
        home: "COL", away: "DAL", goals_home: 4, goals_away: 2, last_period: "REG", p_home: 0.604 }],
    }),
  });
  await open(page, "#/");
  await page.reload(); // zmena len za # by appku znova nenačítala
  const toast = page.locator("#toasts .toast.hit");
  await expect(toast).toContainText("Tip vyšiel DAL 2 : 4 COL");
  await expect(toast).toContainText("sledovaný zápas · tip COL 60 %");
  expect(await page.evaluate(() => localStorage.getItem("tp-follow"))).toBe("[]");
});

test("Detail zápasu NHL: Zdieľať pošle odkaz na zápas", async ({ page }) => {
  await page.addInitScript(() => {
    (window as unknown as { shared: unknown[] }).shared = [];
    Object.defineProperty(navigator, "share", {
      value: async (d: unknown) => (window as unknown as { shared: unknown[] }).shared.push(d),
      configurable: true,
    });
  });
  await nhl(page, "#/nhl/zapas/2026020201");
  await page.getByRole("button", { name: "Zdieľať zápas" }).click();
  const shared = await page.evaluate(() => (window as unknown as { shared: { title: string; url: string }[] }).shared);
  expect(shared).toHaveLength(1);
  expect(shared[0].url).toMatch(/#\/nhl\/zapas\/2026020201$/);
  expect(shared[0].title).toBe("DAL @ COL · Team Pulse");
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
  await expect(page.locator(".tipbox")).toContainText("COL vyhrá");
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
