import type { AppData } from "../data";
import { esc, header, pct1, signed } from "../ui";

const WEIGHT_LABELS: Record<string, string> = {
  home: "Domáce prostredie",
  away_b2b: "Hostia: 2. zápas za 2 dni",
  home_b2b: "Domáci: 2. zápas za 2 dni",
  away_altitude: "Hostia: hrajú vo výške",
  home_missing: "Domáci: chýbajúca kvalita (1 bod PIE)",
  away_missing: "Hostia: chýbajúca kvalita (1 bod PIE)",
  home_tz_east: "Domáci: posun na východ (1 h)",
  strength_diff: "Rozdiel síl súpisiek (1 bod PIE)",
};

function calibration(d: AppData): string {
  const cal = d.model.calibration;
  if (!cal.length) return `<p class="small muted">Kalibrácia bude k dispozícii po pretrénovaní modelu.</p>`;
  const W = 320, H = 170, pad = 28;
  const x = (v: number) => pad + ((v - 0.5) / 0.5) * (W - pad - 10);
  const y = (v: number) => H - pad - ((v - 0.5) / 0.5) * (H - pad - 10);
  const grid = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    .map((v) => `<line x1="${pad}" x2="${W - 10}" y1="${y(v)}" y2="${y(v)}" class="grid"/><text x="${pad - 5}" y="${y(v) + 3}" text-anchor="end" class="axis-lbl">${Math.round(v * 100)}</text>`)
    .join("");
  const pts = cal.map((c) => `${x(c.pred).toFixed(1)},${y(c.actual).toFixed(1)}`).join(" ");
  const dots = cal
    .map((c) => `<circle cx="${x(c.pred).toFixed(1)}" cy="${y(c.actual).toFixed(1)}" r="4" class="dot"><title>predpoveď ${pct1(c.pred)}, skutočnosť ${pct1(c.actual)}, ${c.n} zápasov</title></circle>`)
    .join("");
  return `<svg class="cal" viewBox="0 0 ${W} ${H}" role="img" aria-label="Kalibrácia: predpoveď favorita verzus skutočná úspešnosť v ${cal.length} pásmach">
      ${grid}<line x1="${x(0.5)}" y1="${y(0.5)}" x2="${x(1)}" y2="${y(1)}" class="diag"/>
      <polyline points="${pts}" class="trend"/>${dots}
      <text x="${W - 10}" y="${H - 6}" text-anchor="end" class="axis-lbl">PREDPOVEĎ FAVORITA % →</text></svg>
    <table class="table"><caption class="sr-only">Kalibrácia po pásmach</caption>
      <thead><tr><th>Pásmo</th><th class="n">Zápasy</th><th class="n">Predpoveď</th><th class="n">Skutočnosť</th></tr></thead>
      <tbody>${cal.map((c) => `<tr><td>${Math.round(c.pred * 100)} %</td><td class="n">${c.n.toLocaleString("sk-SK")}</td><td class="n">${pct1(c.pred)}</td><td class="n">${pct1(c.actual)}</td></tr>`).join("")}</tbody></table>`;
}

export function modelView(d: AppData): string {
  const m = d.model;
  const t = m.test_metrics;
  const best = m.versions.length ? m.versions[m.versions.length - 1].model : "";
  const versions = m.versions
    .map((v) => `<tr class="${v.model === best ? "best" : ""}"><td>${esc(v.model)}</td><td class="n">${pct1(v.accuracy)}</td><td class="n">${v.log_loss.toFixed(4).replace(".", ",")}</td></tr>`)
    .join("");
  // Váhy sú z pohľadu domácich; pre „Hostia: …“ otočíme znamienko, aby číslo bolo vplyv na dotknutý team.
  const weights = Object.entries(m.elo_weights)
    .filter(([k]) => k in WEIGHT_LABELS)
    .map(([k, v]) => [k, k.startsWith("away_") ? -v : v] as const)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .map(([k, v]) => `<div class="reason"><span>${esc(WEIGHT_LABELS[k])}</span><span class="num ${v >= 0 ? "pos" : "neg"}">${signed(Math.round(v))}</span></div>`)
    .join("");
  return `${header(`MODEL ${esc(m.version)}`, "PRESNOSŤ", `test ${esc(t.test_seasons)}`)}
    <section class="card metrics">
      <div><div class="big">${pct1(t.accuracy)}</div><div class="small muted">správny víťaz na zápasoch, ktoré model nevidel</div></div>
      <div class="right"><div class="mid num">${t.log_loss.toFixed(4).replace(".", ",")}</div><div class="small muted">log loss</div></div>
    </section>
    <p class="small muted">Tréning: ${m.train_seasons[0] - 1}/${String(m.train_seasons[0]).slice(-2)} – ${m.train_seasons[1] - 1}/${String(m.train_seasons[1]).slice(-2)}, ${m.n_games.toLocaleString("sk-SK")} zápasov. Aj stávkové kancelárie trafia víťaza len v 68–70 % zápasov.</p>
    <div class="cols"><div>
    <h2 class="section">// KALIBRÁCIA</h2><section class="card"><p class="small muted">Keď model povie 70 %, vyjde to naozaj 7 z 10? Bodky blízko prerušovanej čiary = áno.</p>${calibration(d)}</section>
    </div><div>
    <h2 class="section">// VRSTVY MODELU</h2>
    <section class="card"><table class="table"><thead><tr><th>Model</th><th class="n">Presnosť</th><th class="n">Log loss</th></tr></thead><tbody>${versions}</tbody></table></section>
    <h2 class="section">// ČO SA MODEL NAUČIL · VPLYV NA TEAM (ELO)</h2><section class="card">${weights}</section>
    </div></div>`;
}
