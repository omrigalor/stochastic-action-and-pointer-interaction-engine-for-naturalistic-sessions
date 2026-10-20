"""Render the repository overview without third-party plotting dependencies."""

from __future__ import annotations

from html import escape
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from naturalistic_interaction_engine import NaturalisticInteractionEngine  # noqa: E402


WIDTH, HEIGHT = 1200, 720
COLORS = {
    "bezier": "#6ee7d8",
    "wind": "#f6c177",
    "sigma_lognormal": "#8fb5ff",
    "minimum_jerk": "#df91f2",
}


def path_data(points, left, top, width, height):
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, 1)
    span_y = max(max_y - min_y, 1)
    coords = []
    for p in points:
        x = left + (p.x - min_x) / span_x * width
        y = top + (p.y - min_y) / span_y * height
        coords.append((x, y))
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in coords), coords[0], coords[-1]


def main():
    panels = []
    positions = [(70, 220), (620, 220), (70, 465), (620, 465)]
    for index, name in enumerate(COLORS):
        generator = NaturalisticInteractionEngine(seed=100 + index)
        _, points = generator.trajectory((0, 0), (760, 280), model=name, hz=90)
        left, top = positions[index]
        path, start, end = path_data(points, left + 28, top + 57, 454, 92)
        panels.append(
            f'<g><rect x="{left}" y="{top}" width="510" height="185" rx="18" fill="#101a28" '
            f'stroke="#27374d"/><text x="{left + 24}" y="{top + 35}" fill="#dce6f3" font-family="ui-monospace, monospace" font-size="17" font-weight="600">'
            f'{escape(name.replace("_", " ").title())}</text><path d="{path}" '
            f'fill="none" stroke="{COLORS[name]}" stroke-width="4" stroke-linecap="round"/>'
            f'<circle cx="{start[0]:.1f}" cy="{start[1]:.1f}" r="5" fill="{COLORS[name]}"/>'
            f'<circle cx="{end[0]:.1f}" cy="{end[1]:.1f}" r="7" fill="#101a28" stroke="{COLORS[name]}" stroke-width="3"/>'
            f'<text x="{left + 24}" y="{top + 170}" fill="#71849e" font-family="ui-sans-serif, system-ui" font-size="13">seeded stochastic draw · {len(points)} samples</text></g>'
        )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Stochastic Action and Pointer Interaction Engine for Naturalistic Sessions model overview</title>
  <desc id="desc">Four stochastic cursor trajectories generated from the same start and target.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#07111f"/><stop offset="1" stop-color="#111b2e"/></linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="18"/></filter>
  </defs>
  <rect width="1200" height="720" rx="28" fill="url(#bg)"/>
  <circle cx="980" cy="70" r="160" fill="#4177ff" opacity=".10" filter="url(#glow)"/>
  <text x="70" y="70" fill="#f4f7fb" font-family="ui-sans-serif, system-ui" font-size="32" font-weight="700">Stochastic Action and Pointer Interaction Engine</text>
  <text x="70" y="108" fill="#f4f7fb" font-family="ui-sans-serif, system-ui" font-size="32" font-weight="700">for Naturalistic Sessions</text>
  <text x="70" y="168" fill="#7f93ad" font-family="ui-monospace, monospace" font-size="17">KINEMATICS  ·  DWELL  ·  SESSION DEPTH  ·  INTER-SESSION PAUSES</text>
  {''.join(panels)}
</svg>'''
    output = ROOT / "assets" / "naturalistic-interaction-engine-overview.svg"
    output.write_text(svg)
    print(output)


if __name__ == "__main__":
    main()
