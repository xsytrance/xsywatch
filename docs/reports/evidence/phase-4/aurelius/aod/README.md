# AURELIUS — WO-P7 always-on-display luminance evidence

Official Wear OS quality requirement **WO-P7**, not the house heuristic.

> Has an Always on Display mode and illuminates no more than 15% of
> pixels. This is calculated as the average value across the watch face,
> with a fully-opaque white pixel having a value of 100% and a black pixel
> 0%. RGB colors are interpolated linearly between these two values. This
> check is repeated at approximately 10 minute intervals from the start to
> the end of a whole day, and every calculation must satisfy the 15%
> limit.

Source: <https://developer.android.com/docs/quality-guidelines/wear-app-quality>
· checked 2026-07-26.

## Result

| | |
|---|---|
| Visual version | `field-tourbillon-mk2-rc1` (proposed) |
| Samples | 144, at 10-minute intervals, 00:00 → 23:50 |
| Sensitivity runs | 14 (day, battery, heart rate) |
| Worst time sample | 00:50 — 3.952% |
| **Maximum overall** | **3.972%** |
| Limit | 15% |
| **Verdict** | **PASS** |

Reproduce: `python3 tools/aod_luminance.py aurelius --report docs/reports/evidence/phase-4/aurelius/aod`

## How this differs from the old figure

The repository previously reported "≈7% lit pixels". That is a **count of
pixels above a 15/255 threshold on a single frame** — a different quantity
from an average luminance sampled across a day, and it was never
compliance evidence. Both numbers now exist and are labelled: the house
heuristic remains a quick studio signal, and this file is the gate.

## Interpretation choices

The wording admits more than one reading. This gate takes the strictest
available in each case, and says so rather than picking the flattering one:

- **Metric** — computed three ways: unweighted channel mean on encoded
  sRGB, Rec.709 luma on encoded sRGB, and Rec.709 luma after linearising
  sRGB. The gate reports the **largest**.
- **Region** — averaged over the circular display disc (r=240), excluding
  the black canvas corners a round watch never shows. Excluding
  guaranteed-black pixels **raises** the average, so this is stricter than
  averaging the full square; the full-square figure is recorded alongside
  each sample.
- **Time-dependent content** — ambient pins second and millisecond to zero
  (observed Watch7 behaviour), so what varies across a day is the hour and
  minute hands and anything they drive. Inputs that change AOD pixels but
  are not time-of-day — date, battery (reserve needle) and heart rate,
  including the ≤30 bpm fallback — are swept separately at the worst time
  sample.

## Files

| File | What |
|---|---|
| `wo_p7_luminance.json` | every sample, sensitivity run, max and verdict |
| `README.md` | this summary |

Gate implementation: `tools/aod_luminance.py`.
Deliberate-failure fixtures: `tests/visual/test_aod_luminance.py` — 17
tests covering the metric anchors (white = 100%, black = 0%, mid-grey
interpolates linearly), region selection, rejection of over-limit faces,
and validation that the committed evidence really covers a whole day and
declares `pass` only when it passes.
