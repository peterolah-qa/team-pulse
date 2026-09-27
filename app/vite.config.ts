import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { defineConfig, type Plugin } from "vite";

// Po builde dá service workeru novú verziu cache, aby sa po deployi načítala nová appka.
function stampServiceWorker(): Plugin {
  return {
    name: "stamp-sw",
    apply: "build",
    closeBundle() {
      const file = resolve(__dirname, "dist/sw.js");
      const stamp = new Date().toISOString().replace(/[-:.TZ]/g, "");
      writeFileSync(file, readFileSync(file, "utf8").replace("__BUILD__", stamp));
    },
  };
}

// Relatívna cesta: appka funguje lokálne aj na https://<user>.github.io/team-pulse/
export default defineConfig({
  base: "./",
  build: { outDir: "dist", emptyOutDir: true },
  server: { port: 5173 },
  plugins: [stampServiceWorker()],
});
