/* PNG ikony appky z SVG (scripts/make_icons.py) cez Chromium z Playwrightu – rovnaké vykreslenie
   ako v prehliadači, bez ďalších nástrojov. Spustenie: npm run icons */
import { chromium } from "@playwright/test";
import { readFileSync } from "node:fs";

const JOBS = [
  ["public/icon.svg", 512, "public/icon-512.png"],
  ["public/icon.svg", 192, "public/icon-192.png"],
  ["icons/maskable.svg", 512, "public/icon-maskable-512.png"],
  ["icons/ios.svg", 180, "public/apple-touch-icon.png"],
];

const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 1 });
for (const [src, size, out] of JOBS) {
  const data = Buffer.from(readFileSync(src, "utf8")).toString("base64");
  await page.setViewportSize({ width: size, height: size });
  await page.setContent(
    `<body style="margin:0;background:transparent"><img id="i" src="data:image/svg+xml;base64,${data}" width="${size}" height="${size}" style="display:block"></body>`,
  );
  await page.locator("#i").evaluate((img) => img.decode());
  await page.screenshot({ path: out, omitBackground: true, clip: { x: 0, y: 0, width: size, height: size } });
  console.log(`${out}  ${size}×${size}`);
}
await browser.close();
