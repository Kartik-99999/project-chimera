# Convergence Sigil — visual prototype (branch: `signature-experience`)

Isolated full-screen particle study for Project Chimera, composed as a
five-stage editorial research experience. Not wired into the Research
Console; frozen evidence, manifests, routes, and console code are
untouched.

## Launch

Serve the repo root over HTTP (ES modules + `fetch` need it):

```
cd /Users/kartikbhardwaj/project-chimera
python3 -m http.server 8123 --bind 127.0.0.1
```

Open `http://127.0.0.1:8123/research/sigil/`.

## The five stages

One continuous scroll parameter drives the whole journey: it rises
0→1 from Convergence to Exploration, then returns 1→0 so the visit
resolves on the sigil it started from. A fixed stage rail tracks
progress and jumps between stages.

- **A — Convergence.** The particle sigil (instrument ring, gauge
  ticks, evidence hexagon with vertex nodes, three tapered streams,
  small intense core) above the headline, with a live evidence
  signature (2 manifests · 4 runs · 6 audit plans · 3 reports ·
  16 validated relations) and an interaction guide. Hero framing is
  measured from the text block so the ring always clears it.
- **B — Separation.** The ring peels into streams and the arms
  diverge while the hexagon holds. A live layer readout (ring /
  streams / hexagon / core: holding → transit → arrived) is
  derived from the real morph windows.
- **C — Assembly.** Particles seat into the real 15 entities; each
  of the 16 validated edges fades in only after both endpoints
  arrive. A live readout counts seated entities and drawn
  relations. Copy explains the validated chain: runs execute
  manifests, plans sample runs, reports cite runs.
- **D — Exploration.** The settled constellation with staggered
  labels, 2D de-collision, neighbor highlighting on selection, a
  working detail panel with real console links, and substring
  search across label, id, and kind (Enter selects, Esc clears).
- **E — Resolution.** The field returns to the sigil beside closing
  copy, a console entry link, and a back-to-top link.

Missing evidence is handled honestly: the page adds a
`no-evidence` class revealing notices in stages B/C, the signature
and readouts state the failure, and search disables.

## Files

- `engine.js` — DOM-free layout + field math (unit-tested),
  including scroll/camera tracks, alpha gates, layer states, and
  the node filter.
- `sigil.js` — Canvas 2D spring renderer, scroll/input/a11y wiring.
- `sigil.css`, `index.html` — page shell (canvas never intercepts
  input; labels are real `<button>`s; `Esc` clears selection).
- `engine.test.mjs` — 14 tests (`node --test`).
- `shots/` — key-state screenshots from headless Chrome.

## Evaluation (editorial pass, Chrome 156 headless)

- 19 scripted states: dispersed opening, formed sigil, cursor dent,
  all five stage centers, selection, search filter/select/clear,
  mobile hero/assembly/exploration/resolution (390×844),
  reduced-motion hero/constellation/resolution.
- Hero clearance measured in-page: ring bottom stays above the
  text top on desktop (328<347) and mobile (367<431).
- Interactions exercised: cursor displacement (parked p95 0.25 vs
  calm 0.035), scroll through every stage, click selection with
  neighbor highlight, Tab + Enter/Space activation, search with
  live count, rail anchors, resize across viewports. All panel,
  CTA, console, and rail links verified real.
- 0 console/page errors; 60 fps during live render (4200 particles).
- Reduced motion: single static frame per scroll position, no rAF
  loop; rail anchors jump between stages.
- `window.__sigil` exposes sim state for demos/debugging.

## Honest limitations

- The hero sigil shrank as the opening gained content (scale ~147
  at 1440×813) — presence traded for guaranteed clearance.
- Mobile stage bands stack above the field rather than beside it;
  small screens get sequence where desktops get juxtaposition.
- No interaction demo video was recorded (CDP stills only).
- Touch was verified only via emulated mobile viewport, not a
  physical device.
