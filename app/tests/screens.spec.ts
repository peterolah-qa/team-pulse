import { expect, test, type Page } from "@playwright/test";
import { open, serveData, withResults } from "./helpers";

/* Nový vzhľad (20. 10. 2026): pás dní, balíček kariet zápasov, prehľad dňa, Tipy s ukazovateľmi,
   Teamy ako 4 úrovne formy, NHL karty z rozpadu tipu. „Teraz“ = streda 21. 10. 0:30 (helpers.NOW). */
test.beforeEach(async ({ page }) => {
  await serveData(page, { predictions: withResults });
});

const mobile = (info: { project: { name: string } }) => info.project.name === "mobile";
const nums = (texts: string[]) => texts.map((t) => Number(t.replace("−", "-").replace(",", ".").replace(/[^\d.+-]/g, "")));

async function zapasy(page: Page, hash = "#/") {
  await open(page, hash);
  await page.locator(".dstrip").waitFor();
  await page.evaluate(() => document.fonts.ready); // po načítaní písma sa karty preskladajú a karusel sa prichytí znova
}

test("Zápasy: predvolené sú karty, pás dní s počtom zápasov a najistejším tipom", async ({ page }) => {
  await zapasy(page);
  const chips = page.locator(".dchip");
  await expect(chips).toHaveCount(3);
  await expect(chips.locator(".dc-t")).toHaveText(["Dnes", "Zajtra", "pi"]);
  await expect(chips.nth(0)).toHaveAttribute("aria-pressed", "true");
  await expect(chips.nth(0).locator(".dc-n")).toHaveText("3 zápasy");
  await expect(chips.nth(0).locator(".dc-tip")).toHaveText("NYK 84 %");
  await expect(chips.nth(2).locator(".dc-n")).toHaveText("1 zápas");
  await expect(page.locator(".seg [aria-pressed=true]")).toHaveText("Karty");
  const cards = page.locator(".mcard");
  await expect(cards).toHaveCount(3);
  await expect(cards.first()).toHaveAttribute("aria-label", "Zápas 1 z 3: BOS @ DET");
  await expect(cards.first().locator(".mside.fav .ms-abbr")).toHaveText("DET");
  await expect(cards.first().locator(".ms-p")).toHaveText(["38 %", "62 %"]);
  await expect(cards.first().locator(".mtip")).toHaveText(/DET\s*vyhrá so šancou\s*62 %/);
  // Pulse ako prstenec a číslo pri oboch teamoch
  await expect(cards.first().locator(".tb.ringed")).toHaveCount(2);
  await expect(cards.first().locator(".ms-line").first()).toContainText("Pulse 42");
  // dôvody v prospech tipu: chýbajúci hráč súpera tipu pomáha
  await expect(cards.first().locator(".mreasons li")).toHaveText([/DET: Sila súpisky\s*\+14/, /BOS: Bez I\. Varga \(\?\)\s*\+12/]);
  await expect(cards.first().locator(".mc-more")).toHaveAttribute("href", "#/zapas/0022600001");
});

test("Zápasy: iný deň v páse ukáže jeho zápasy a prehľad dňa", async ({ page }) => {
  await zapasy(page);
  const side = page.locator(".dash-side");
  await expect(side.locator(".widget").first().locator(".kpi-n")).toHaveText(["3", "67 %", "28 %"]); // 62 · 84 · 54 % ≈ 28 %
  await expect(side.locator(".toptip")).toContainText("NYK");
  await expect(side.locator(".toptip .tipp")).toHaveText("84 %");
  await expect(side.locator(".tierlegend li")).toHaveText([/Silní\s*1/, /Stabilní\s*2/, /Oslabení\s*4/, /Kritickí\s*1/]);
  await page.locator(".dchip").nth(1).click();
  await expect(page.locator(".dchip").nth(1)).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".mcard")).toHaveCount(2);
  await expect(page.locator(".mcard").first()).toHaveAttribute("aria-label", "Zápas 1 z 2: NYK @ BOS");
  await expect(side.locator(".widget").first().locator(".kpi-n").first()).toHaveText("2");
  await expect(side.locator(".toptip")).toContainText("DEN");
});

test("Zápasy: balíček kariet na mobile – poradie, šípky, švih; na počítači mriežka", async ({ page }, info) => {
  await zapasy(page);
  const track = page.locator(".deck-track");
  if (!mobile(info)) {
    await expect(page.locator(".deck-top")).toBeHidden();
    expect(await track.evaluate((el) => getComputedStyle(el).gridTemplateColumns.split(" ").length)).toBe(2);
    return;
  }
  const pos = page.locator(".deck-pos");
  await expect(pos).toHaveText("Zápas 1 z 3");
  await expect(page.getByRole("button", { name: "Predchádzajúci zápas" })).toBeDisabled();
  await page.getByRole("button", { name: "Ďalší zápas" }).click();
  await expect(pos).toHaveText("Zápas 2 z 3");
  await expect(page.locator(".deck-prog i.on")).toHaveCount(2);
  await expect(page.locator(".mcard").nth(1)).toBeInViewport({ ratio: 0.8 });
  // švih = vodorovné posunutie balíčka
  await track.evaluate((el) => el.scrollTo({ left: el.scrollWidth, behavior: "instant" as ScrollBehavior }));
  await expect(pos).toHaveText("Zápas 3 z 3");
  await expect(page.getByRole("button", { name: "Ďalší zápas" })).toBeDisabled();
  // klávesnica
  await track.focus();
  await page.keyboard.press("ArrowLeft");
  await expect(pos).toHaveText("Zápas 2 z 3");
});

test("Zápasy: prepínač Karty / Zoznam si appka pamätá, v zozname pás dní posunie na deň", async ({ page }) => {
  await zapasy(page);
  await page.locator(".seg button", { hasText: "Zoznam" }).click();
  await expect(page.locator(".seg [aria-pressed=true]")).toHaveText("Zoznam");
  await expect(page.locator("a.match")).toHaveCount(6);
  await expect(page.locator(".mcard")).toHaveCount(0);
  await page.reload();
  await expect(page.locator("a.match")).toHaveCount(6);
  await page.locator(".dchip").nth(2).click();
  await expect(page.locator("#den-2026-10-23")).toBeInViewport();
  await page.locator(".seg button", { hasText: "Karty" }).click();
  await expect(page.locator(".mcard")).toHaveCount(1); // zvolený deň ostal
});

test("Tipy: ukazovatele, stĺpce šancí a súčin pri každom riadku", async ({ page }) => {
  await open(page, "#/tipy");
  const kpis = page.locator(".kpi-card");
  await expect(kpis.nth(0)).toContainText("NYK");
  await expect(kpis.nth(0).locator(".kpi-n")).toHaveText("84 %");
  await expect(kpis.nth(1).locator(".kpi-n")).toHaveText("6");
  await expect(kpis.nth(2).locator(".kpi-n")).toHaveText("8 %");
  await expect(page.locator("svg.acc-chart .pbar")).toHaveCount(6);
  expect(await page.locator(".tiprow").nth(1).locator(".accbar i").evaluate((el) => (el as HTMLElement).style.width)).toBe("61%");
});

test("Teamy: 4 úrovne formy, poradie podľa Pulse, posun oproti normálu", async ({ page }, info) => {
  await open(page, "#/teamy");
  const panels = page.locator(".tpanel");
  await expect(panels.locator(".tp-h > span:first-child")).toHaveText(["Silní", "Stabilní", "Oslabení", "Kritickí"]);
  await expect(panels.locator(".tp-r")).toHaveText(["Pulse 70 a viac", "Pulse 50 – 69", "Pulse 30 – 49", "Pulse pod 30"]);
  const rows = page.locator("a.teamrow");
  await expect(rows.locator(".rank")).toHaveText(["1", "2", "3", "4", "5", "6", "7", "8"]);
  await expect(rows.locator(".abbr")).toHaveText(["NYK", "OKC", "SAS", "DET", "DEN", "BOS", "PHI", "LAL"]);
  const pulses = nums(await rows.locator(".pulse").allTextContents());
  expect([...pulses].sort((a, b) => b - a)).toEqual(pulses);
  await expect(panels.nth(2).locator(".teamrow").nth(2).locator(".shift")).toHaveText("dnes −3 Elo · Bez I. Varga (?) −12");
  await expect(panels.nth(0).locator(".shift")).toHaveText("dnes +16 Elo · Sila súpisky +16");
  await expect(rows.first().locator(".tb.ringed")).toHaveCount(1);
  if (mobile(info)) {
    const tabs = page.locator(".ttab");
    await expect(tabs).toHaveText([/Silní\s*1/, /Stabilní\s*2/, /Oslabení\s*4/, /Kritickí\s*1/]);
    await expect(panels.nth(2)).not.toBeInViewport();
    await tabs.nth(2).click();
    await expect(tabs.nth(2)).toHaveAttribute("aria-pressed", "true");
    await expect(panels.nth(2)).toBeInViewport({ ratio: 0.9 });
  } else {
    for (const p of await panels.all()) await expect(p).toBeInViewport(); // 4 stĺpce vedľa seba
  }
  await rows.nth(1).click();
  await expect(page).toHaveURL(/#\/team\/OKC$/);
});

test("NHL Zápasy: karty s rozpadom tipu v prospech favorita, aréna, prstenec = šanca", async ({ page }) => {
  await zapasy(page, "#/nhl/");
  await page.locator(".beta-note").first().waitFor();
  const cards = page.locator(".mcard");
  await expect(cards).toHaveCount(2); // dnes BUF @ TOR a DAL @ COL
  const buf = cards.first();
  await expect(buf).toHaveAttribute("aria-label", "Zápas 1 z 2: BUF @ TOR");
  await expect(buf.locator(".mside.fav .ms-abbr")).toHaveText("BUF");
  await expect(buf.locator(".mreasons li")).toHaveText([/Rozdiel v Elo\s*\+59,5/, /TOR: domáci ľad\s*−20,0/, /Konštanta modelu a drobné vplyvy\s*−13,4/]);
  const col = cards.nth(1);
  await expect(col.locator(".mc-venue")).toHaveText("Ball Arena");
  await expect(col.locator(".ms-line").first()).toContainText("3-2-1");
  await expect(col.locator(".mreasons li")).toHaveText([/COL: back-to-back\s*−42,5/, /Rozdiel v Elo\s*\+41,2/, /DAL: back-to-back\s*\+38,5/, /COL: domáci ľad\s*\+20,0/]);
  await expect(page.locator(".dash-side")).toContainText("Najsilnejší podľa Ela");
});
