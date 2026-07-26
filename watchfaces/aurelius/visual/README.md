# Aurelius visual contract (ADR-009)

Machine-checkable visual identity for the engine-managed Aurelius face.
Born from the Phase-2 WARBIRD incident: structural gates cannot prove the
intended pixels ship, so approved pixels are a tested contract here.

```text
states.toml    fixed, fully-pinned render states + comparison policy
goldens/       APPROVED reference renders, one directory per visual version
               (replacing anything here REQUIRES a matching approved record
                in approvals/ — enforced by tools/validate.py)
candidates/    proposed renders for a new visual version; no approval needed
               to exist, but they can never overwrite goldens/
masks/         comparison masks (white = compared, black = ignored) for
               legitimately dynamic / non-capturable regions; subject to the
               min-disc-coverage policy in states.toml
inventories/   deterministic resource inventory (JSON + Markdown) binding
               every runtime resource byte to the visual version
approvals/     machine-readable intentional-visual-change records
```

Tooling (repo root):

```bash
python3 tools/inventory_resources.py aurelius            # regenerate
python3 tools/inventory_resources.py aurelius --check    # CI drift gate
python3 tools/render_reference.py aurelius --state normal_hero --out out.png
python3 tools/render_reference.py aurelius --goldens --check   # golden gate
python3 tools/compare_visuals.py a.png b.png --report diff/    # metrics+heatmap
python3 tools/validate.py                                # includes visual checks
```

The reference renderer composes the committed generated XML plus committed
`res/` bytes (the closest reviewable artifact to the runtime), evaluating the
face's WFF expression subset at the pinned state. Known renderer/runtime
differences are documented in `tools/render_reference.py` module docs and
matter only for device-capture comparisons, which use the calibrated
perceptual profile in `states.toml`.
