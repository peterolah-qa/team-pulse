/* Model: ako často trafí víťaza, či sedia percentá (kalibrácia), podrobnosti po rozkliknutí. */
import type { AppData, ModelInfo } from "../data";
import { esc, header, pct1, signed } from "../ui";

const n4 = (x: number): string => x.toFixed(4).replace(".", ",");

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

function calibration(m: ModelInfo): string {
  const cal = m.calibration;
  if (!cal.length) return `<p class="muted">Kalibrácia bude k dispozícii po pretrénovaní modelu.</p>`;
  const W = 320, H = 180, padL = 42, padB = 28, padT = 10, padR = 12;
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

/* Prínos vrstiev: log loss každej verzie (menej = lepšie) a zmena oproti predchádzajúcej. */
function layers(m: ModelInfo): string {
  const v = m.versions;
  if (!v.length) return "";
  const lo = Math.min(...v.map((x) => x.log_loss)), hi = Math.max(...v.map((x) => x.log_loss));
  const span = Math.max(hi - lo, 0.001);
  const rows = v
    .map((x, i) => {
      const w = 30 + ((hi - x.log_loss) / span) * 70; // kratší pruh = horší log loss
      const d = i ? x.log_loss - v[i - 1].log_loss : 0;
      const best = i === v.length - 1;
      return `<li class="${best ? "best" : ""}"><div class="ly-top"><span class="ly-name">${esc(x.model)}</span><span class="num">${n4(x.log_loss)}</span></div>
        <div class="ly-bar" aria-hidden="true"><i style="width:${w.toFixed(0)}%"></i></div>
        <div class="ly-sub"><span>presnosť ${pct1(x.accuracy)}</span>${i ? `<span class="${d < 0 ? "pos" : d > 0 ? "neg" : "muted"}">${d < 0 ? "−" : d > 0 ? "+" : "±"}${n4(Math.abs(d))}</span>` : `<span class="muted">základ</span>`}</div></li>`;
    })
    .join("");
  return `<h2 class="sec">Prínos vrstiev</h2><section class="card"><ol class="layers">${rows}</ol>
    <p class="small muted">Log loss na testovacích sezónach, menej = lepšie. Dlhší pruh = lepší model. Vrstva sa do modelu dostala, len ak zlepšila log loss aspoň o 0,0005.</p></section>`;
}

/* Spoločná obrazovka modelu; šport dodá popisy váh a vetu pod presnosťou. */
export function modelPage(m: ModelInfo, labels: Record<string, string>, intro: string, extra = ""): string {
  const t = m.test_metrics;
  const weights = Object.entries(m.elo_weights)
    .filter(([k]) => k in labels)
    .map(([k, v]) => [k, k.startsWith("away_") ? -v : v] as const)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .map(([k, v]) => `<li><span>${esc(labels[k])}</span><span class="num ${v >= 0 ? "pos" : "neg"}">${signed(Math.round(v))}</span></li>`)
    .join("");
  const seasons = `${m.train_seasons[0] - 1}/${String(m.train_seasons[0]).slice(-2)} – ${m.train_seasons[1] - 1}/${String(m.train_seasons[1]).slice(-2)}`;
  return `${header("Model", `verzia ${esc(m.version)} · test na sezónach ${esc(t.test_seasons)}`)}${extra}
    <div class="kpis-row">
      <div class="card kpi-card main"><span class="label">Presnosť</span><span class="big-n num">${pct1(t.accuracy)}</span><span class="kpi-l">trafený víťaz v zápasoch, ktoré model pri učení nevidel</span></div>
      <div class="card kpi-card"><span class="label">Log loss</span><span class="kpi-n num">${n4(t.log_loss)}</span><span class="kpi-l">istota percent, menej = lepšie</span></div>
      <div class="card kpi-card"><span class="label">Brier</span><span class="kpi-n num">${n4(t.brier)}</span><span class="kpi-l">chyba percent, menej = lepšie</span></div>
    </div>
    <p class="hint intro">${intro}</p>
    <h2 class="sec">Kalibrácia: sedia percentá?</h2><section class="card">${calibration(m)}</section>
    ${layers(m)}
    <details class="more"><summary>Čo sa model naučil</summary>
      <p class="small muted">Učenie na sezónach ${seasons}, ${m.n_games.toLocaleString("sk-SK")} zápasov. Vplyv na team v Elo bodoch:</p>
      <ul class="rows">${weights}</ul>
    </details>`;
}

export function modelView(d: AppData): string {
  return modelPage(d.model, WEIGHT_LABELS, "Aj stávkové kancelárie trafia víťaza len v 68 – 70 % zápasov.");
}
