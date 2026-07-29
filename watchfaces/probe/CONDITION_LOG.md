# WEATHER.CONDITION — observed integers

The whole point of the probe. Read the `COND` row and the name under it, and
add a line. One line per distinct name seen; if the same name shows a
different integer on a different day, add that as a second line rather than
editing the first — a disagreement is data.

Nothing downstream needs this table to be complete. Every state in the plan's
§3 ladder works without it; the decode only *adds* fog, mist, thunder, hail
and sleet, which are not derivable from the numeric sources at all.

| `CONDITION` | `CONDITION_NAME` | `IS_DAY` | date seen | notes |
|---|---|---|---|---|
| | | | | |

## Forecast — does it populate

Fill in once, the first time the probe is worn with weather available. This is
the answer that unblocks the plan's open decision 6 (a forecast instrument on
COMMODORE PRO).

| Reading | Row on face | Observed | Notes |
|---|---|---|---|
| `WEATHER.WEATHER.UV_INDEX` (doubled prefix) | `UV` → `V4:` | | 0 or blank suggests it is a schema typo nothing implements |
| `WEATHER.HOURS.0.UV_INDEX` | `UV` → `H0:` | | |
| `WEATHER.HOURS.0.IS_AVAILABLE` | `H+0` → `AV:` | | |
| `WEATHER.HOURS.3.IS_AVAILABLE` | `H+3` → `AV:` | | if H+0 populates and H+3 does not, only index 0 is real |
| `WEATHER.DAYS.1.IS_AVAILABLE` | `D+1` → `AV:` | | |
| do the forecast `CONDITION`s use the same integers as the current one | `H+0 C:` vs `COND` | | if yes, one decode covers both |

## The two negative results expected

Record these too — a confirmed no is worth as much as a yes, and both are
currently inferences rather than observations.

| Question | Expectation | Observed |
|---|---|---|
| Does the complication slot's value drive anything? | **No** — the format exposes no readable complication source | |
| Does the sun compass read as an instrument? | unknown — this is a judgement call, not a measurement | |
