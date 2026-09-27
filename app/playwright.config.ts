import { defineConfig, devices } from "@playwright/test";

/* Testy bežia proti produkčnému buildu (vite preview). Dáta sa podstrčia z tests/fixtures,
   takže výsledok nezávisí od dnešných zápasov. Vizuálne testy len s VISUAL=1 (a v CI). */
const visual = !!process.env.VISUAL;

export default defineConfig({
  testDir: "tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://localhost:4173",
    locale: "sk-SK",
    timezoneId: "Europe/Bratislava",
    serviceWorkers: "block", // inak by service worker obišiel podstrčené dáta
    trace: "retain-on-failure",
  },
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.02, animations: "disabled" } },
  projects: [
    { name: "mobile", testIgnore: /visual/, use: { ...devices["Pixel 7"] } },
    { name: "desktop", testIgnore: /visual/, use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } } },
    ...(visual
      ? [
          { name: "visual-mobile", testMatch: /visual/, use: { ...devices["Pixel 7"] } },
          { name: "visual-desktop", testMatch: /visual/, use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } } },
        ]
      : []),
  ],
  webServer: {
    command: "npm run build && npm run preview",
    url: "http://localhost:4173",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
