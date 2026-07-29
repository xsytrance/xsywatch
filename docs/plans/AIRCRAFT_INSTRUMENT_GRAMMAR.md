# Aircraft instrument grammar

**The technique, documented as asked.** If it is approved this becomes the
house method for every gauge in the collection, and the five existing faces
get retrofitted to it.

Implementation: `tools/make_an_gauge.py`. That module is the executable copy
of this document; if the two ever disagree, the module is right.

---

## 1. The reference, and why this one

**North American P-51D Mustang — the AN (Army-Navy) engine instruments.**

Chosen over the Spitfire's RAF blind-flying panel, the Bf 109's Askania
instruments and an F-14's mixed panel for one practical reason that has
nothing to do with taste:

> **AN instruments are a written specification, not just a look.**

That turns "model it as closely as possible" into a checkable exercise. Every
proportion below can be argued from the standard rather than from a mood
board, and a later face can be held to the same rule.

The Mustang also happens to carry the whole vocabulary on small round dials —
tachometer, manifold pressure, oil and fuel — which is exactly the form factor
a watch sub-dial is.

---

## 2. The grammar — twelve elements

This list *is* the technique. Anything that follows all twelve reads as an
aircraft instrument. Anything that takes half of them reads as a generic dial
with ticks on it, which is what the collection had before.

Drawn in this order:

| # | Element | Why it is there on the real thing |
|---|---|---|
| 1 | **Well** | the recess the instrument sits in; the rim shadows into the top of it because a cockpit is lit from above |
| 2 | **Dial face** | matte, near-black, barely graded. **Never glossy** — gloss on a panel is glare, and glare is dangerous |
| 3 | **Range arcs** | green normal / yellow caution / red limit |
| 4 | **Graduations** | majors long and thick, **four minors between them** — five divisions per major is the AN convention |
| 5 | **Redline** | a radial bar at never-exceed, drawn over the arcs |
| 6 | **Numerals** | at majors only, and only as many as fit |
| 7 | **Index mark** | a luminous triangle at the scale origin — radium then, tritium later |
| 8 | **Legend** | the quantity and its unit, small, in the gap at the bottom of the sweep |
| 9 | **Counter** | the digital window |
| 10 | **Pointer** | a thin shaft widening to a **spade** near the tip, with a counterbalance tail |
| 11 | **Hub** | a domed cap with a highlight, hiding the pointer's root |
| 12 | **Glass** | one soft diagonal highlight at low alpha |

### The two elements that matter most

**The range arcs (3) are the single most recognisable feature of an aircraft
gauge, and the only one that carries meaning rather than decoration.** They
are also why this was worth doing rather than just prettying up the old
dials: green/yellow/red maps directly onto the data we already have.

- **Pulse** — the arcs *are* heart-rate zones. Resting band green, working
  amber, red above 160, redline at 180.
- **Steps** — the arcs *are* goal progress, with the polarity deliberately
  inverted: sedentary is the red end and the goal is the green one. The
  meaning is preserved even though the direction is not.

So the most authentic feature is also the most useful one. That is the whole
argument for copying a real instrument instead of inventing a dial.

**The counter (9) is authentic, and this surprised me.** A big number inside
a round gauge looks like a modern intrusion, but an altimeter carries a drum
counter for thousands of feet right beside its pointer for hundreds. Reading
a precise value off a window while reading a *rate* off a pointer is
period-correct. That is what makes "big legible numbers" and "a faithful
aircraft gauge" compatible rather than opposed.

---

## 3. Recolouring

The brief was to keep the real thing's structure and move the colours onto
the face. So:

- The arcs keep their **meaning and their order** — safe, caution, limit —
  and move onto the dial's palette. COMMODORE's teal-green, amber and red
  rather than aviation's primaries.
- Graduations go near-white; numerals and legend go the dial's amber.
- The pointer becomes a **hot orange-red that appears nowhere else on the
  face**. This is a legibility rule, not a style one: on the base faces the
  needle was the same amber as the numerals, so the one moving thing in the
  well was camouflaged against the printed scale it exists to be read
  against.
- **Red stays red.** It is the one colour on an instrument that must not be
  restyled — it means "stop" everywhere in aviation and always has.

---

## 4. Sizing, and the mistake worth not repeating

The sub-dials were 61px because that is the size of the wells painted into
the plate. Making the numbers legible needed bigger gauges, and the plate
looked like a hard constraint.

**It was not.** The window's *bounding box* is 140×140 at (170, 293), which
leaves about 25px of clearance — but the window is an **arch**, and its real
extent measured off its own alpha channel starts at y=320 and is inset
either side. Actual clearance from each sub-dial centre is **60px and 66px**.

So the gauges went to **96px**, drawing their own bezel over the plate's
smaller printed one. A 57% increase that was available the whole time and was
hidden by trusting a rectangle instead of measuring the shape.

> **Measure the alpha, not the bounding box.**

### What the readouts actually gained

| Readout | Before | After | Note |
|---|---|---|---|
| Pulse | 18 | **27** | two digits, readable at arm's length |
| Date | 19 | **24** | |
| Reserve | 18 | **22** | |
| Steps | 17 | **19** | five digits have to fit the counter window |

Steps gains least and that is a real limit, not an oversight: a number that
overflows its window is worse than a smaller one. Four or five digits will
never be as readable as two at this dial size. If steps needs to be bigger
than this, the honest fix is to show it in hundreds against the `X100`
legend the gauge already carries — which is, again, what a real instrument
does.

---

## 5. What this does not fix

**The wells are still dark because the plate is still generated art.** Every
improvement here is drawn *on top of* COMMODORE's plate. The gauges are now
provenance-clean and so is the window, but the plate and the hands are not,
and the plate is what keeps the sub-dials sitting in murk.

The next real step is a **procedural plate**, which would:

- put the sub-dial wells wherever the layout wants them, at whatever size;
- let the readouts be as large as legibility asks rather than as large as
  the painted wells allow;
- and finish the provenance job — window, gauges and plate all original by
  construction, which is the whole face.

---

## 6. Applying it elsewhere

`make_an_gauge.py` takes its scale markings as **fractions of the sweep**
(0..1) rather than degrees, so an instrument can be re-scaled without moving
its markings by hand. Adding a gauge is a dict:

```python
"bpm": dict(
    label="PULSE", unit="BPM",
    numerals=[(0.0, "0"), (1.0, "200")],
    arcs=[(0.20, 0.50, "arc_ok"), (0.50, 0.80, "arc_warn"),
          (0.80, 1.0, "arc_lim")],
    redline=0.90),
```

Per face, only `PALETTE` changes. HAYATE would go white-on-black with a red
pointer; HOG-WILD wants the A-10's black-and-green. **The grammar does not
change between faces — only the hues do.** That is what makes it a house
method rather than one face's styling.
