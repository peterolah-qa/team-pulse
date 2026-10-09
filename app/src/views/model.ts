/* Model: ako často trafí víťaza, či sedia percentá (kalibrácia), podrobnosti po rozkliknutí. */
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
  if (!cal.length) return `<p class="muted">Kalibrácia bude k dispozícii po pretrénovaní modelu.</p>`;
  const W = 320, H = 180, padL = 34, padB = 28, padT = 10, padR = 12;
  const x = (v: number) => padL + ((v - 0.5) / 0.5) * (W - padL - padR);
  const y = (v: number) => H - padB - ((v - 0.5) / 0.5) * (H - padB - padT);
  const ticks = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0];
  const grid = ticks
    .map((v) => `<line x1="${padL}" x2="${W - padR}" y1="${y(v)}" y2="${y(v)}" class="grid"/><text x="${padL - 6}" y="${y(v) + 3}" text-anchor="end" class="axis-lbl">${Math.round(v * 100)} %</text>`)
    .join("");
  const xt = ticks.map((v) => `<text x="${x(v)}" y="${H - padB + 14}" text-anchor="middle" class="axis-lbl">${Math.round(v * 100)}</text>`).join("");
  const pts = cal.map((c) => `${x(c.pred).toFixed(1)},${y(c.actual).toFixed(1)}`).join(" ");
  const dots = cal
    .map((c) => `<circle cx="${x(c.pred).toFixed(1)}" cy="${y(c.actual).toFixed(1)}" r="4" class="dot"><title>model ${pct1(c.pred)}, skutočnosť ${pct1(c.actual)}, ${c.n} zápasov</title></circle>`)
    .join("");
  return `<svg class="cal" viewBox="0 0 ${W} ${H}" role="img" aria-label="Kalibrácia: šanca favorita podľa modelu verzus ako často favorit naozaj vyhral, ${cal.length} pásiem">
      ${grid}${xt}<line x1="${x(0.5)}" y1="${y(0.5)}" x2="${x(1)}" y2="${y(1)}" class="diag"/>
      <polyline points="${pts}" class="trend"/>${dots}</svg>
    <p class="small muted">Vodorovne: šanca favorita podľa modelu. Zvislo: ako často favorit naozaj vyhral. Bodky na čiare = percentá sedia.</p>`;
}

export function modelView(d: AppData): string {
  const m = d.model;
  const t = m.test_metrics;
  const versions = m.versions
    .map((v, i) => `<tr class="${i === m.versions.length - 1 ? "best" : ""}"><td>${esc(v.model)}</td><td class="n">${pct1(v.accuracy)}</td><td class="n">${v.log_loss.toFixed(4).replace(".", ",")}</td></tr>`)
    .join("");
  const weights = Object.entries(m.elo_weights)
    .filter(([k]) => k in WEIGHT_LABELS)
    .map(([k, v]) => [k, k.startsWith("away_") ? -v : v] as const)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .map(([k, v]) => `<li><span>${esc(WEIGHT_LABELS[k])}</span><span class="num ${v >= 0 ? "pos" : "neg"}">${signed(Math.round(v))}</span></li>`)
    .join("");
  const seasons = `${m.train_seasons[0] - 1}/${String(m.train_seasons[0]).slice(-2)} – ${m.train_seasons[1] - 1}/${String(m.train_seasons[1]).slice(-2)}`;
  return `${header("Model", `verzia ${esc(m.version)}`)}
    <section class="card hero">
      <p class="big-n num">${pct1(t.accuracy)}</p>
      <p>Toľko zápasov model trafil (víťaza) v sezónach ${esc(t.test_seasons)}, ktoré pri učení nevidel. Aj stávkové kancelárie trafia víťaza len v 68 – 70 % zápasov.</p>
    </section>
    <h2 class="sec">Sedia percentá?</h2><section class="card">${calibration(d)}</section>
    <details class="more"><summary>Ako sa model učil</summary>
      <p class="small muted">Učenie na sezónach ${seasons}, ${m.n_games.toLocaleString("sk-SK")} zápasov. Každá vrstva musela zlepšiť presnosť, inak sa nepoužila.</p>
      <table class="table"><caption class="sr-only">Porovnanie vrstiev modelu</caption><thead><tr><th>Vrstvy</th><th class="n">Presnosť</th><th class="n">Log loss</th></tr></thead><tbody>${versions}</tbody></table>
      <p class="small muted sub-h">Čo sa model naučil (vplyv na team v Elo bodoch)</p><ul class="rows">${weights}</ul>
    </details>`;
}
