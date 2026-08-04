"""Reusable WFF scene-component factories.

Each factory returns a `Component`: the WFF elements plus machine-checkable
metadata (motion class, AOD policy, referenced resources). The engine owns
behavior and structure; it never owns face art — every image resource name
is supplied by the face spec.

Extraction basis (PHASE_2_COMPONENT_AUDIT): parallax (9 faces), analog hand
angles (4–5 faces), smooth-elapsed rotation (4 faces), battery/date/HR
bindings (6–7 faces), sheen breathing (3 faces).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import expressions as X
from .model import Elem, inline
from .profiles import AmbientPolicy, MotionClass


@dataclass
class Component:
    name: str
    kind: str
    motion_class: MotionClass
    aod: AmbientPolicy
    elems: list[Elem] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    notes: str = ""


def _part_image(name: str, box: dict, resource: str, alpha: int = 255,
                pivot: bool | tuple[float, float] = False) -> Elem:
    attrs = {"name": name, "x": str(box["x"]), "y": str(box["y"]),
             "width": str(box["width"]), "height": str(box["height"]),
             "alpha": str(alpha)}
    if pivot is True:
        attrs["pivotX"] = "0.5"
        attrs["pivotY"] = "0.5"
    elif pivot:
        # Six places, not four: a shared pivot is usually a repeating
        # fraction, and rounding it early leaves layers that are meant to roll
        # together a fraction of a pixel apart.
        attrs["pivotX"] = f"{pivot[0]:.6f}".rstrip("0").rstrip(".")
        attrs["pivotY"] = f"{pivot[1]:.6f}".rstrip("0").rstrip(".")
    p = Elem("PartImage", attrs)
    return p


def _shared_pivot(part_box: dict, about_x: float, about_y: float
                  ) -> tuple[float, float]:
    """Pivot fractions that put a part's rotation centre on an absolute point.

    Layers that roll together must roll about the SAME point. A scrolling
    overlay is deliberately longer than the scene it covers and is drawn
    offset from it, so its own centre is somewhere else entirely — pivoting
    both at 0.5 swings them about centres up to a tile apart, and the weather
    visibly slides across the view it is supposed to be falling through.
    """
    return ((about_x - part_box["x"]) / part_box["width"],
            (about_y - part_box["y"]) / part_box["height"])


def _finish(part: Elem, aod: AmbientPolicy, transforms: list[Elem],
            resource: str) -> Elem:
    part.child(aod.variant())
    for t in transforms:
        part.child(t)
    part.child(Elem("Image", {"resource": resource}))
    return part


def _transform(target: str, value: str) -> Elem:
    return Elem("Transform", {"target": target, "value": value})


FULLSCREEN = {"x": 0, "y": 0, "width": 480, "height": 480}


def background_pair(normal_res: str, aod_res: str,
                    parallax_amp: tuple[float, float] | None = None,
                    fade: float = 0.6) -> list[Component]:
    """Normal/AOD background crossfade; optional accelerometer parallax on
    the normal layer. AOD layer is static (no motion in ambient)."""
    normal = _part_image("z00_bg", FULLSCREEN, normal_res, alpha=255)
    normal.child(AmbientPolicy(0, fade, 0.0, "EASE_OUT").variant())
    if parallax_amp:
        ax, ay = parallax_amp
        normal.child(_transform("x", X.parallax_offset(0, ax, "X")))
        normal.child(_transform("y", X.parallax_offset(0, ay, "Y")))
    normal.child(Elem("Image", {"resource": normal_res}))

    aod = _part_image("z01_aod", FULLSCREEN, aod_res, alpha=0)
    aod.child(AmbientPolicy(255, fade, 0.0, "EASE_IN").variant())
    aod.child(Elem("Image", {"resource": aod_res}))

    return [
        Component("z00_bg", "background", MotionClass.AMBIENT_MOTION,
                  AmbientPolicy(0, fade, 0.0, "EASE_OUT"), [normal],
                  [normal_res], "normal-mode background w/ parallax"),
        Component("z01_aod", "background-aod", MotionClass.STATIC,
                  AmbientPolicy(255, fade, 0.0, "EASE_IN"), [aod],
                  [aod_res], "ambient background revealed in AOD"),
    ]


def rotating_image(name: str, resource: str, box: dict,
                   speed_deg_per_sec: float, aod: AmbientPolicy,
                   reverse: bool = False, ratio_note: str = "") -> Component:
    """Continuously rotating mechanical layer with explicit direction and
    documented speed. Mechanically-coupled ratios are recorded in metadata
    so meshed gears keep believable relationships."""
    part = _part_image(name, box, resource, pivot=True)
    _finish(part, aod,
            [_transform("angle",
                        X.rotation_continuous(speed_deg_per_sec, reverse))],
            resource)
    direction = "CCW" if reverse else "CW"
    return Component(name, "rotating-image", MotionClass.MECHANICAL, aod,
                     [part], [resource],
                     f"{speed_deg_per_sec} deg/s {direction}. {ratio_note}".strip())


def seconds_rotor(name: str, resource: str, box: dict,
                  aod: AmbientPolicy) -> Component:
    """One full rotation per minute, millisecond-smoothed (tourbillon cage,
    seconds hands)."""
    part = _part_image(name, box, resource, pivot=True)
    _finish(part, aod, [_transform("angle", X.seconds_angle())], resource)
    return Component(name, "seconds-rotor", MotionClass.TIME_CRITICAL, aod,
                     [part], [resource], "360deg per minute")


def tap_sequence(name: str, resources: list[str], box: dict,
                 aod: AmbientPolicy, frame_rate: int = 24,
                 loop_count: int = 1,
                 before: str = "HIDE", after: str = "HIDE") -> Component:
    """A frame sequence that plays when the wearer taps the face.

    WFF v4 exposes exactly one interaction hook: AnimationController's `play`
    trigger, whose vocabulary is TAP / ON_VISIBLE / ON_NEXT_SECOND /
    ON_NEXT_MINUTE / ON_NEXT_HOUR (common/simpleTypes/eventTriggerType.xsd).
    There is no pointer position, no drag, no long-press and no per-region
    hit testing: a tap anywhere in this part's bounding box fires it.

    `before`/`after` are frameOptionType — DO_NOTHING, FIRST_FRAME, THUMBNAIL
    or HIDE. Defaulting both to HIDE gives a burst that is invisible until
    provoked and leaves nothing behind, which is what a muzzle flash wants.

    NOTE ON SOUND: the format has no audio element at any version through 5.
    A watch face ships no code (hasCode=false), so it cannot drive the
    speaker however capable the hardware is. This component is the closest
    the format allows — a visual report, silent.
    """
    if not resources:
        raise ValueError(f"{name}: tap_sequence needs at least one frame")
    if not 1 <= frame_rate <= 60:
        raise ValueError(f"{name}: frameRate {frame_rate} outside WFF 1..60")
    valid = {"DO_NOTHING", "FIRST_FRAME", "THUMBNAIL", "HIDE"}
    for label, opt in (("before", before), ("after", after)):
        if opt not in valid:
            raise ValueError(f"{name}: {label}Playing {opt!r} not in {valid}")

    part = Elem("PartAnimatedImage", {
        "name": name, "x": str(box["x"]), "y": str(box["y"]),
        "width": str(box["width"]), "height": str(box["height"]),
        "pivotX": "0.5", "pivotY": "0.5",
    })
    part.child(aod.variant())
    part.child(Elem("AnimationController", {
        "play": "TAP",
        "loopCount": str(loop_count),
        "beforePlaying": before,
        "afterPlaying": after,
    }))
    seq = Elem("SequenceImages", {"frameRate": str(frame_rate),
                                  "loopCount": str(loop_count)})
    for res in resources:
        seq.child(Elem("Image", {"resource": res}))
    part.child(seq)
    return Component(name, "tap-sequence", MotionClass.EVENT, aod,
                     [part], list(resources),
                     f"{len(resources)} frames @ {frame_rate}fps on TAP; "
                     f"before={before} after={after}")


def weather_scene(name: str, box: dict, aod: AmbientPolicy,
                  clear: str, overcast: str, rain: str, snow: str,
                  night: str, rain_pct: int = 50, showers_pct: int = 20,
                  snow_temp: int = 2, roll_gain_deg: float = 0.0,
                  pitch_gain_px: float = 0.0, roll_clamp_deg: int = 45,
                  pitch_clamp_deg: int = 40) -> Component:
    """The cockpit window, showing the wearer's actual weather.

    WFF v4 carries native weather sources — WEATHER.IS_DAY,
    WEATHER.CHANCE_OF_PRECIPITATION, WEATHER.TEMPERATURE and the rest — so
    this needs no complication provider and no companion app.

    WHY THIS BRANCHES ON NUMBERS AND NOT ON WEATHER.CONDITION: the schema
    declares CONDITION as a source but documents none of its integer values.
    Branching on an undocumented enum would be guessing, and guessing wrong
    shows the wearer snow in July. IS_DAY, CHANCE_OF_PRECIPITATION and
    TEMPERATURE are numerically unambiguous, so the tree is built from those.

    Order matters: WFF renders the FIRST Compare that matches, so the tests
    run most-specific first. If weather is unavailable or erroring, nothing
    matches and Default renders the clear scene — the face never shows an
    empty window.
    """
    # WFF requires each Compare to name a declared Expression rather than
    # carry inline arithmetic, so every branch test is declared up front.
    tests = [
        ("wx_night", "[WEATHER.IS_AVAILABLE] && ![WEATHER.IS_DAY]", night),
        ("wx_snow", "[WEATHER.IS_AVAILABLE] && "
                    "[WEATHER.CHANCE_OF_PRECIPITATION] >= %d && "
                    "[WEATHER.TEMPERATURE] <= %d" % (rain_pct, snow_temp), snow),
        ("wx_rain", "[WEATHER.IS_AVAILABLE] && "
                    "[WEATHER.CHANCE_OF_PRECIPITATION] >= %d" % rain_pct, rain),
        ("wx_dull", "[WEATHER.IS_AVAILABLE] && "
                    "[WEATHER.CHANCE_OF_PRECIPITATION] >= %d" % showers_pct,
         overcast),
    ]

    cond = Elem("Condition", {})
    exprs = Elem("Expressions", {})
    for nm, val, _res in tests:
        e = Elem("Expression", {"name": nm})
        e.text = val
        exprs.child(e)
    cond.child(exprs)

    # Branch parts are mutually exclusive — only the first matching Compare
    # ever renders — but the z-order check reads document order, so they are
    # numbered to keep it monotonic.
    seq = [0]

    moving = roll_gain_deg or pitch_gain_px

    def scene(res):
        part = _part_image(f"{name}_{seq[0]}_{res}", box, res,
                           pivot=bool(moving))
        seq[0] += 1
        part.child(aod.variant())
        if moving:
            # roll is negated so the horizon appears to stay level while the
            # instrument turns around it, which is what a real gyro does
            part.child(_transform("angle",
                                  X.parallax_offset(0, -roll_gain_deg, "X",
                                                    roll_clamp_deg)))
            part.child(_transform("y",
                                  X.parallax_offset(box["y"], pitch_gain_px,
                                                    "Y", pitch_clamp_deg)))
        part.child(Elem("Image", {"resource": res}))
        return part

    for nm, _val, res in tests:
        cmp_ = Elem("Compare", {"expression": nm})
        cmp_.child(scene(res))
        cond.child(cmp_)

    default = Elem("Default", {})
    default.child(scene(clear))
    cond.child(default)

    cls = MotionClass.AMBIENT_MOTION if moving else MotionClass.EVENT
    how = ("wrist-reactive field, roll %.0fdeg pitch %.0fpx" %
           (roll_gain_deg, pitch_gain_px)) if moving else "static scene"
    return Component(name, "weather-scene", cls, aod, [cond],
                     [clear, overcast, rain, snow, night],
                     f"live weather in the cockpit window ({how}); falls back "
                     "to clear when the source is unavailable")


def _gyro(roll_deg: float, x_px: float, y_px: float,
          roll_clamp: int = 45, shift_clamp: int = 40) -> Elem | None:
    """A <Gyro>: wrist-driven adjustment of a part, in one element.

    WHY THIS AND NOT MORE Transforms. The format carries a dedicated Gyro
    element (common/transform/gyroElements.xsd) that takes x, y, scaleX,
    scaleY, angle and alpha together, and its values are *relative* — the
    schema's own example yields +/-5, which only makes sense as a delta. That
    matters twice over: the expression carries no base term, so it cannot
    fight the part's position, and it leaves the Transform targets free for
    time-driven motion. Scrolling rain that also tilts needs both, and two
    Transforms on the same target cannot deliver it.

    Every axis is guarded by ACCELEROMETER_IS_SUPPORTED. A watch without the
    sensor reports a constant, and a layer displaced by a constant is simply
    in the wrong place for good.
    """
    attrs: dict[str, str] = {}
    if roll_deg:
        # Negated: the horizon should appear to stay level while the
        # instrument turns around it, which is what the real one does.
        attrs["angle"] = X.if_accelerometer(
            X.tilt_shift(-roll_deg, "X", roll_clamp))
    if x_px:
        attrs["x"] = X.if_accelerometer(X.tilt_shift(x_px, "X", shift_clamp))
    if y_px:
        attrs["y"] = X.if_accelerometer(X.tilt_shift(y_px, "Y", shift_clamp))
    return Elem("Gyro", attrs) if attrs else None


# Condition tests, most specific first. WFF renders the FIRST Compare that
# matches, so order is the logic.
#
# WHY THESE BRANCH ON NUMBERS AND NOT ON WEATHER.CONDITION: the schema
# declares CONDITION as a source but documents none of its integer values.
# Branching on an undocumented enum is guessing, and guessing wrong shows the
# wearer snow in July. IS_DAY, CHANCE_OF_PRECIPITATION and TEMPERATURE are
# numerically unambiguous.
#
# Night is tested first on purpose: a lit daytime sky at 3am is a worse error
# than a rainy night rendered without its rain.
def _weather_tests(rain_pct: int, showers_pct: int, storm_pct: int,
                   snow_temp: int) -> list[tuple[str, str]]:
    av = "[WEATHER.IS_AVAILABLE]"
    return [
        ("wx_night", f"{av} && ![WEATHER.IS_DAY]"),
        ("wx_snow", f"{av} && [WEATHER.CHANCE_OF_PRECIPITATION] >= {rain_pct}"
                    f" && [WEATHER.TEMPERATURE] <= {snow_temp}"),
        ("wx_storm", f"{av} && [WEATHER.CHANCE_OF_PRECIPITATION] >= {storm_pct}"),
        ("wx_rain", f"{av} && [WEATHER.CHANCE_OF_PRECIPITATION] >= {rain_pct}"),
        ("wx_dull", f"{av} && [WEATHER.CHANCE_OF_PRECIPITATION] >= {showers_pct}"),
    ]


def animated_weather(name: str, box: dict, aod: AmbientPolicy,
                     scenes: dict[str, str], overlays: dict[str, str],
                     tile: int, periods: dict[str, float] | None = None,
                     roll_gain_deg: float = 0.0, shift_x_px: float = 0.0,
                     shift_y_px: float = 0.0, clip: str | None = None,
                     clip_box: dict | None = None,
                     rain_pct: int = 50, showers_pct: int = 20,
                     storm_pct: int = 75, snow_temp: int = 2,
                     roll_clamp_deg: int = 45, shift_clamp_deg: int = 40,
                     flash: str | None = None, aperture: bool = False,
                     flash_period_s: float = 12.0) -> Component:
    """The cockpit window, showing live weather that actually moves.

    Each branch is a scene, an overlay scrolling across it, and — in the
    storm branch — a lightning wash driven on alpha.

    HOW THE MOTION IS BUILT. Precipitation is one seamlessly tiling sprite
    translated by exactly its tile period, not a frame sequence: a sequence
    at this size would cost twenty-odd PNGs per condition per face, and it
    would judder whenever the watch throttled its refresh. A translation is
    smooth at any frame rate the device feels like giving it.

    The scroll goes on a Transform and the wrist response on a Gyro, so the
    two compose instead of contending for one target.

    CLIPPING IS THE CALLER'S PROBLEM AND THIS CHECKS IT. WFF has no mask, so
    an overlay is confined only by something opaque above it. A face whose
    window is an aperture through the plate (HAYATE) needs nothing. A face
    that draws its window over an opaque plate must pass `clip`, and this
    refuses to build without one — an unclipped overlay does not fail subtly,
    it rains across the whole dial.
    """
    periods = dict(periods or {})
    tests = _weather_tests(rain_pct, showers_pct, storm_pct, snow_temp)
    known = {t[0] for t in tests} | {"wx_clear"}

    for key in set(scenes) | set(overlays):
        if key not in known:
            raise ValueError(f"{name}: unknown weather branch {key!r}; "
                             f"expected any of {sorted(known)}")
    if overlays and clip is None and not aperture:
        raise ValueError(
            f"{name}: animated overlays need either a plate aperture above "
            f"them or a clip sprite. Pass clip=... (see "
            f"tools/make_window_clips.py) or aperture=true if the plate "
            f"already carries a hole. Without one the weather escapes "
            f"across the dial.")
    if clip is not None and clip_box is None:
        raise ValueError(f"{name}: clip {clip!r} given without clip_box")

    ox, oy = box["x"], box["y"]
    bw, bh = box["width"], box["height"]
    # Zero-padded: the face validator checks that z-prefixed names ascend in
    # document order, and it compares them as strings, so an unpadded _10_
    # sorts before _2_ and trips the check.
    seq = [0]

    def branch(key: str) -> list[Elem]:
        """Scene, then weather over it, then the surround that traps it."""
        out: list[Elem] = []
        gy = _gyro(roll_gain_deg, shift_x_px, shift_y_px,
                   roll_clamp_deg, shift_clamp_deg)

        def emit(part: Elem, res: str, transforms: list[Elem]) -> None:
            part.child(aod.variant())
            if gy is not None:
                part.child(Elem("Gyro", dict(gy.attrs)))
            for t in transforms:
                part.child(t)
            part.child(Elem("Image", {"resource": res}))
            out.append(part)

        scene_res = scenes.get(key)
        if scene_res:
            emit(_part_image(f"{name}_{seq[0]:02d}_scene", box, scene_res,
                             pivot=True), scene_res, [])
            seq[0] += 1

        ov = overlays.get(key)
        if ov:
            horizontal = key == "wx_dull"       # cloud drifts sideways
            period = periods.get(key, 2.4)
            if horizontal:
                obox = {"x": ox - tile, "y": oy, "width": bw + tile,
                        "height": bh}
                tf = _transform("x", f"{X.num(ox - tile)} + "
                                     f"{X.scroll_offset(tile, period)}")
            else:
                obox = {"x": ox, "y": oy - tile, "width": bw,
                        "height": bh + tile}
                tf = _transform("y", f"{X.num(oy - tile)} + "
                                     f"{X.scroll_offset(tile, period)}")
            # Roll about the window's centre, not the overlay sprite's own.
            piv = _shared_pivot(obox, ox + bw / 2.0, oy + bh / 2.0)
            emit(_part_image(f"{name}_{seq[0]:02d}_wx", obox, ov, pivot=piv),
                 ov, [tf])
            seq[0] += 1

        if flash and key == "wx_storm":
            emit(_part_image(f"{name}_{seq[0]:02d}_flash", box, flash, alpha=255,
                             pivot=True), flash,
                 [_transform("alpha", X.flash_alpha(255, 14.0, flash_period_s))])
            seq[0] += 1

        if clip is not None:
            # Last in the branch, so it is above everything it must trap.
            cp = _part_image(f"{name}_{seq[0]:02d}_clip", clip_box, clip)
            cp.child(aod.variant())
            cp.child(Elem("Image", {"resource": clip}))
            out.append(cp)
            seq[0] += 1
        return out

    cond = Elem("Condition", {})
    exprs = Elem("Expressions", {})
    for nm, val in tests:
        e = Elem("Expression", {"name": nm})
        e.text = val
        exprs.child(e)
    cond.child(exprs)

    for nm, _val in tests:
        cmp_ = Elem("Compare", {"expression": nm})
        for el in branch(nm):
            cmp_.child(el)
        cond.child(cmp_)

    default = Elem("Default", {})
    for el in branch("wx_clear"):
        default.child(el)
    cond.child(default)

    used = sorted({r for r in list(scenes.values()) + list(overlays.values())
                   if r} | ({flash} if flash else set())
                  | ({clip} if clip else set()))
    moving = bool(roll_gain_deg or shift_x_px or shift_y_px)
    how = (f"roll {roll_gain_deg:.0f}deg, shift {shift_x_px:.0f}/"
           f"{shift_y_px:.0f}px" if moving else "no wrist response")
    return Component(name, "animated-weather", MotionClass.AMBIENT_MOTION, aod,
                     [cond], used,
                     f"live weather, animated on a {tile}px scroll tile; "
                     f"{how}; falls back to clear when the source is "
                     f"unavailable")


def radar_weather(name: str, box: dict, aod: AmbientPolicy,
                  light: str, heavy: str, roll_gain_deg: float = 0.0,
                  shift_x_px: float = 0.0, shift_y_px: float = 0.0,
                  rain_pct: int = 50, showers_pct: int = 20,
                  storm_pct: int = 75, snow_temp: int = 2,
                  breathe_period_s: float = 6.0,
                  roll_clamp_deg: int = 45,
                  shift_clamp_deg: int = 40) -> Component:
    """Precipitation drawn as a PPI radar paints it.

    HOG-WILD has no window to look out of, and giving it one would be giving
    it somebody else's dial. Its six o'clock is a radar scope, and a scope's
    whole job is showing where the weather is — so its returns *are* its
    weather display, not a substitute for one.

    Returns hold station and breathe on alpha rather than scrolling; echoes
    that slide across a scope would be reading out ground speed, which this
    aircraft is not supplying.
    """
    # Dry branches paint nothing, and the schema will not accept that as an
    # empty <Compare> (conditionElement.xsd requires at least one child) nor
    # as an empty <Default>. So a branch that shows no returns is simply not
    # declared: nothing matches, the Condition falls through, and the scope
    # stays dark — which is the correct reading for clear air anyway.
    #
    # Dropping the night branch is what makes a wet night work. Night is
    # tested first in the window faces so they never show a lit sky at 3am,
    # but a radar scope has no sky to light, and leaving night out means a
    # rainy night reaches the rain branch and paints its returns.
    paint = {"wx_snow": (light, 170, 40), "wx_storm": (heavy, 225, 30),
             "wx_rain": (heavy, 200, 45), "wx_dull": (light, 130, 45)}
    tests = [(nm, val) for nm, val
             in _weather_tests(rain_pct, showers_pct, storm_pct, snow_temp)
             if nm in paint]

    cond = Elem("Condition", {})
    exprs = Elem("Expressions", {})
    for nm, val in tests:
        e = Elem("Expression", {"name": nm})
        e.text = val
        exprs.child(e)
    cond.child(exprs)

    gy = _gyro(roll_gain_deg, shift_x_px, shift_y_px, roll_clamp_deg,
               shift_clamp_deg)
    seq = [0]

    def scope(res: str, base: int, amp: int) -> Elem:
        part = _part_image(f"{name}_{seq[0]:02d}_rdr", box, res, pivot=True)
        seq[0] += 1
        part.child(aod.variant())
        if gy is not None:
            part.child(Elem("Gyro", dict(gy.attrs)))
        part.child(_transform("alpha",
                              X.breathing_alpha(base, amp,
                                                6.2831853 / breathe_period_s)))
        part.child(Elem("Image", {"resource": res}))
        return part

    for nm, _val in tests:
        cmp_ = Elem("Compare", {"expression": nm})
        res, base, amp = paint[nm]
        cmp_.child(scope(res, base, amp))
        cond.child(cmp_)

    return Component(name, "radar-weather", MotionClass.AMBIENT_MOTION, aod,
                     [cond], [light, heavy],
                     f"precipitation as radar returns, breathing on a "
                     f"{breathe_period_s}s cycle; blank when dry")


def hr_balance(name: str, resource: str, box: dict, aod: AmbientPolicy,
               center: float = 180, amplitude: float = 35,
               fallback: int = 70, clamp_lo: int = 40,
               clamp_hi: int = 200,
               rad_per_beat: float | str = 0.10472) -> Component:
    """Heart-rate-driven balance-wheel oscillator with fallback + clamp."""
    part = _part_image(name, box, resource, pivot=True)
    expr = X.hr_oscillator_angle(center, amplitude, rad_per_beat,
                                 fallback, clamp_lo, clamp_hi)
    _finish(part, aod, [_transform("angle", expr)], resource)
    return Component(name, "hr-balance", MotionClass.MECHANICAL, aod,
                     [part], [resource],
                     f"±{amplitude}° around {center}°, freq=live HR "
                     f"(fallback {fallback}, clamp {clamp_lo}-{clamp_hi})")


def battery_needle(name: str, resource: str, aod: AmbientPolicy,
                   start_deg: float | str, sweep_deg: float | str,
                   box: dict | None = None) -> Component:
    """Battery power-reserve needle: start..start+sweep over 0..100%."""
    part = _part_image(name, box or FULLSCREEN, resource, pivot=True)
    _finish(part, aod,
            [_transform("angle", X.gauge_angle(start_deg, sweep_deg))],
            resource)
    return Component(name, "battery-needle", MotionClass.TIME_CRITICAL, aod,
                     [part], [resource],
                     f"{start_deg}°..+{sweep_deg}° over 0..100% battery")


def value_needle(name: str, resource: str, aod: AmbientPolicy,
                 start_deg: float | str, sweep_deg: float | str,
                 source: str, lo: int = 0, hi: int = 100,
                 box: dict | None = None) -> Component:
    """A gauge needle driven by any data source, not just battery.

    `battery_needle` is this with the source fixed; the underlying expression
    always supported a clamp range, the component just never exposed it. Step
    counts, altitude, reserve arcs and anything else with a known full-scale
    value now get a real needle instead of a number in a box.
    """
    part = _part_image(name, box or FULLSCREEN, resource, pivot=True)
    _finish(part, aod,
            [_transform("angle", X.gauge_angle(start_deg, sweep_deg,
                                               source, lo, hi))],
            resource)
    return Component(name, "value-needle", MotionClass.TIME_CRITICAL, aod,
                     [part], [resource],
                     f"{start_deg}deg..+{sweep_deg}deg over {source} {lo}..{hi}")


def date_text(name: str, box: dict, aod: AmbientPolicy, font_family: str,
              size: int, color: str, template: str = "%d",
              expression: str = "[DAY]") -> Component:
    """Date aperture rendered with a bitmap font."""
    part = Elem("PartText", {"name": name, "x": str(box["x"]),
                             "y": str(box["y"]), "width": str(box["width"]),
                             "height": str(box["height"])})
    part.child(aod.variant())
    tmpl = Elem("Template", text=template)
    tmpl.child(Elem("Parameter", {"expression": expression}))
    bf = Elem("BitmapFont", {"family": font_family, "size": str(size),
                             "color": color})
    bf.child(tmpl)
    txt = Elem("Text", {"align": "CENTER"})
    txt.child(bf)
    part.child(inline(txt))
    return Component(name, "date-text", MotionClass.TIME_CRITICAL, aod,
                     [part], [], f"template {template!r} on {expression}")


def sheen(name: str, resource: str, aod: AmbientPolicy,
          alpha_base: float, alpha_amp: float, alpha_rad_per_sec: float | str,
          parallax_amp: tuple[float, float] | None = None) -> Component:
    """Breathing specular sheen with optional strong parallax; hidden in AOD."""
    part = _part_image(name, FULLSCREEN, resource, alpha=0)
    transforms = [_transform("alpha", X.breathing_alpha(
        alpha_base, alpha_amp, alpha_rad_per_sec))]
    if parallax_amp:
        ax, ay = parallax_amp
        transforms.append(_transform("x", X.parallax_offset(0, ax, "X")))
        transforms.append(_transform("y", X.parallax_offset(0, ay, "Y")))
    _finish(part, aod, transforms, resource)
    return Component(name, "sheen", MotionClass.AMBIENT_MOTION, aod,
                     [part], [resource], "breathing alpha + parallax")


def analog_hand(name: str, resource: str, aod: AmbientPolicy,
                which: str, alpha: int = 255) -> Component:
    """Fullscreen pre-centered analog hand (hour or minute).

    `alpha` is the NORMAL-mode alpha; 0 with an ambient policy of 255 gives
    an AOD-only hand, so a face can swap in a distinct ambient hand shape
    without losing the time reading.
    """
    angles = {"hour": X.hour_angle(), "minute": X.minute_angle()}
    if which not in angles:
        raise ValueError(f"which must be hour|minute, got {which!r}")
    part = _part_image(name, FULLSCREEN, resource, alpha=alpha, pivot=True)
    _finish(part, aod, [_transform("angle", angles[which])], resource)
    return Component(name, f"hand-{which}", MotionClass.TIME_CRITICAL, aod,
                     [part], [resource], f"analog {which} hand")


def static_image(name: str, resource: str, box: dict,
                 aod: AmbientPolicy, alpha: int = 255) -> Component:
    """Non-moving image layer (hand hub, fixed ornament).

    `alpha` is the NORMAL-mode alpha. Setting it to 0 with an ambient policy
    of 255 gives an AOD-only layer, which is how a face swaps a moving
    normal-mode layer for a frozen ambient one.
    """
    part = _part_image(name, box, resource, alpha=alpha)
    _finish(part, aod, [], resource)
    return Component(name, "static-image", MotionClass.STATIC, aod,
                     [part], [resource], f"normal alpha {alpha}")


def horizon_field(name: str, resource: str, box: dict, aod: AmbientPolicy,
                  roll_gain_deg: float, pitch_gain_px: float,
                  roll_clamp_deg: int = 45, pitch_clamp_deg: int = 40,
                  alpha: int = 255) -> Component:
    """Wrist-reactive artificial-horizon field: roll about the field centre
    plus vertical translation, both driven by the accelerometer.

    The field is deliberately oversized. It is drawn below an opaque plate
    whose only transparent region is the aperture, so the visible result is
    a horizon seen through a porthole. WFF has no mask primitive for
    PartImage; occlusion is the mechanism.

    Roll gain is applied NEGATED: as the wrist rolls one way the field
    counter-rotates, so the horizon appears to stay level.

    Neutral behaviour in AOD is achieved structurally, not by damping this
    layer: pair it with an `aod` policy of alpha 0 and a separate frozen
    ambient field. A hidden layer cannot move.
    """
    part = _part_image(name, box, resource, alpha=alpha, pivot=True)
    _finish(part, aod, [
        _transform("angle", X.parallax_offset(0, -roll_gain_deg, "X",
                                              roll_clamp_deg)),
        _transform("y", X.parallax_offset(box["y"], pitch_gain_px, "Y",
                                          pitch_clamp_deg)),
    ], resource)
    return Component(name, "horizon-field", MotionClass.AMBIENT_MOTION, aod,
                     [part], [resource],
                     f"roll ±{roll_gain_deg}° (negated), pitch ±"
                     f"{pitch_gain_px}px, wrist clamps ±{roll_clamp_deg}°/±"
                     f"{pitch_clamp_deg}°")


def text_line(name: str, box: dict, aod: AmbientPolicy, font_family: str,
              size: int, color: str, template: str,
              expressions_: list[str], align: str = "CENTER",
              gate: str | None = None) -> Component:
    """Generic bitmap-font text line with N parameters (digital time, data
    readouts). Non-Aurelius generalization of date_text, used by fixtures.

    `gate` is an optional boolean expression; when given, the text is wrapped
    in a Condition so it only paints while the expression holds. A readout
    whose source can be absent ([WEATHER.*], [HEART_RATE]) must gate on the
    availability flag, because the template renders an absent source as a
    plausible-looking zero — and a scope legend reading "0%" in weather the
    provider never measured is a lie with confident typography.
    """
    part = Elem("PartText", {"name": name, "x": str(box["x"]),
                             "y": str(box["y"]), "width": str(box["width"]),
                             "height": str(box["height"])})
    part.child(aod.variant())
    tmpl = Elem("Template", text=template)
    for e in expressions_:
        tmpl.child(Elem("Parameter", {"expression": e}))
    bf = Elem("BitmapFont", {"family": font_family, "size": str(size),
                             "color": color})
    bf.child(tmpl)
    txt = Elem("Text", {"align": align})
    txt.child(bf)
    part.child(inline(txt))
    if gate is None:
        return Component(name, "text-line", MotionClass.TIME_CRITICAL, aod,
                         [part], [], f"template {template!r}")
    cond = Elem("Condition", {})
    exprs = Elem("Expressions", {})
    e = Elem("Expression", {"name": f"{name}_gate"})
    e.text = gate
    exprs.child(e)
    cond.child(exprs)
    cmp_ = Elem("Compare", {"expression": f"{name}_gate"})
    cmp_.child(part)
    cond.child(cmp_)
    return Component(name, "text-line", MotionClass.TIME_CRITICAL, aod,
                     [cond], [], f"template {template!r} gated on {gate!r}")
