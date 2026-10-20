"""Ikona appky Team Pulse (Luminous Pulse) ako SVG: squircle, radarové kruhy, neónová EKG krivka
z fialovej cez indigo do azúrovej a smaragdovej (od bežného stavu po Silný) a žiariaci vrcholový uzol.

Tri varianty z jedného návrhu:
  app/public/icon.svg     squircle s priehľadnými rohmi – prehliadač, počítač, ikona „any“
  app/icons/maskable.svg  celý štvorec, obsah v bezpečnej zóne (kruh 80 %) – Android (maskable)
  app/icons/ios.svg       celý štvorec, rohy zaoblí iOS – apple-touch-icon

Spustenie:  uv run python scripts/make_icons.py && (cd app && npm run icons)
            (druhý krok z SVG vyrobí PNG: icon-192, icon-512, icon-maskable-512, apple-touch-icon)
"""

from __future__ import annotations

import math
from pathlib import Path

OUT = {
    "any": Path("app/public/icon.svg"),
    "full": Path("app/icons/maskable.svg"),
    "ios": Path("app/icons/ios.svg"),
}
SCALE = {"any": 1.0, "full": 0.86, "ios": 0.94}  # zmenšenie obsahu, aby ho maska systému neorezala

# EKG krivka v 512 × 512: rovná línia, malý zub, hlboký pokles, vysoký vrchol (Peak Pulse), návrat
PTS = [(70, 292), (176, 292), (206, 254), (238, 346), (282, 138), (322, 292), (442, 292)]
PEAK = PTS[4]


def squircle(n: float = 5.0, steps: int = 144) -> str:
    """Superelipsa |x|^n + |y|^n = 1 (tvar ikon na iOS a Androide), vyplní celý štvorec 512."""
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        c, s = math.cos(t), math.sin(t)
        x = 256 + 256 * math.copysign(abs(c) ** (2 / n), c)
        y = 256 + 256 * math.copysign(abs(s) ** (2 / n), s)
        pts.append(f"{x:.1f} {y:.1f}")
    return "M" + "L".join(pts) + "Z"


def stops(*items: tuple[float, str, float]) -> str:
    return "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in items)


DEFS = f"""<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0.35" y2="1">
    {stops((0, "#14192b", 1), (1, "#05070c", 1))}</linearGradient>
  <radialGradient id="hi" cx="0.5" cy="0.08" r="0.75">
    {stops((0, "#8b5cf6", 0.28), (1, "#8b5cf6", 0))}</radialGradient>
  <linearGradient id="rim" x1="0" y1="0" x2="1" y2="1">
    {stops((0, "#8b5cf6", 1), (0.5, "#6366f1", 0.35), (1, "#00f2fe", 1))}</linearGradient>
  <linearGradient id="pulse" gradientUnits="userSpaceOnUse" x1="70" y1="0" x2="442" y2="0">
    {stops((0, "#8b5cf6", 1), (0.38, "#6366f1", 1), (0.62, "#00f2fe", 1), (1, "#10b981", 1))}</linearGradient>
  <radialGradient id="node" cx=".4" cy=".35" r=".7">
    {stops((0, "#ffffff", 1), (0.45, "#b9fbff", 1), (1, "#00f2fe", 1))}</radialGradient>
  <radialGradient id="halo">{stops((0, "#00f2fe", 0.75), (1, "#00f2fe", 0))}</radialGradient>
  <filter id="wide" x="-20%" y="-40%" width="140%" height="180%"><feGaussianBlur stdDeviation="16"/></filter>
  <filter id="near" x="-20%" y="-40%" width="140%" height="180%"><feGaussianBlur stdDeviation="5"/></filter>
</defs>"""


def background(kind: str) -> str:
    if kind != "any":
        return (
            '<rect width="512" height="512" fill="url(#bg)"/><rect width="512" height="512" fill="url(#hi)"/>'
        )
    path = squircle()
    rim = 'transform="translate(256 256) scale(0.988) translate(-256 -256)"'  # okraj celý vnútri tvaru
    return (
        f'<path d="{path}" fill="url(#bg)"/><path d="{path}" fill="url(#hi)"/>'
        f'<path d="{path}" {rim} fill="none" stroke="url(#rim)" stroke-width="5" stroke-opacity=".75"/>'
    )


def artwork() -> str:
    pts = " ".join(f"{x},{y}" for x, y in PTS)
    px, py = PEAK
    line = f'<polyline points="{pts}" stroke="url(#pulse)"'
    return f"""<g fill="none" stroke="#8b5cf6" stroke-width="3">
    <circle cx="256" cy="268" r="82" stroke-opacity=".22"/>
    <circle cx="256" cy="268" r="146" stroke-opacity=".15"/>
    <circle cx="256" cy="268" r="210" stroke-opacity=".09"/>
    <path d="M256 58v420M46 268h420" stroke-opacity=".07" stroke-dasharray="6 10"/>
  </g>
  <g fill="none" stroke-linecap="round" stroke-linejoin="round">
    {line} stroke-width="44" opacity=".55" filter="url(#wide)"/>
    {line} stroke-width="30" opacity=".9" filter="url(#near)"/>
    {line} stroke-width="28"/>
    <polyline points="{pts}" stroke="#ffffff" stroke-width="7" stroke-opacity=".5"/>
  </g>
  <circle cx="{px}" cy="{py}" r="58" fill="url(#halo)"/>
  <circle cx="{px}" cy="{py}" r="23" fill="url(#node)"/>"""


def svg(kind: str) -> str:
    s = SCALE[kind]
    t = f' transform="translate(256 256) scale({s}) translate(-256 -256)"' if s != 1.0 else ""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">\n<title>Team Pulse</title>\n'
        f"{DEFS}\n{background(kind)}\n<g{t}>\n  {artwork()}\n</g>\n</svg>\n"
    )


def main() -> None:
    for kind, path in OUT.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg(kind), encoding="utf-8")
        print(f"{path}  ({kind})")


if __name__ == "__main__":
    main()
