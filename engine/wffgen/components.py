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
                pivot: bool = False) -> Elem:
    attrs = {"name": name, "x": str(box["x"]), "y": str(box["y"]),
             "width": str(box["width"]), "height": str(box["height"]),
             "alpha": str(alpha)}
    if pivot:
        attrs["pivotX"] = "0.5"
        attrs["pivotY"] = "0.5"
    p = Elem("PartImage", attrs)
    return p


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
              expressions_: list[str], align: str = "CENTER") -> Component:
    """Generic bitmap-font text line with N parameters (digital time, data
    readouts). Non-Aurelius generalization of date_text, used by fixtures."""
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
    return Component(name, "text-line", MotionClass.TIME_CRITICAL, aod,
                     [part], [], f"template {template!r}")
