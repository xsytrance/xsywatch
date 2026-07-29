"""WFF arithmetic-expression builders.

Every builder returns the exact expression string that goes into a
`Transform`/`Parameter` attribute. Number formatting is explicit and
deterministic: ints render bare, floats render via repr-trimming so the same
input always yields the same text.

The canonical time base is `elapsed_seconds()` — smooth wall-clock seconds
including milliseconds — which the Aurelius audit showed underlies gears,
oscillators, and sheen across multiple faces.
"""

from __future__ import annotations


def num(value: float | int | str) -> str:
    """Deterministic number rendering: 6 -> '6', 6.0 -> '6.0', '45.0' kept."""
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    return repr(float(value))


def elapsed_seconds() -> str:
    """Smooth seconds within the hour (drives mechanical motion)."""
    return "[MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000"


def seconds_precise() -> str:
    """Smooth seconds within the minute."""
    return "[SECOND] + [MILLISECOND] / 1000"


def hour_angle() -> str:
    """Analog hour-hand angle, minute-smoothed (30°/hour)."""
    return "([HOUR_0_11] + [MINUTE] / 60) * 30"


def minute_angle() -> str:
    """Analog minute-hand angle, second-smoothed (6°/minute)."""
    return "([MINUTE] + [SECOND] / 60) * 6"


def seconds_angle() -> str:
    """Seconds angle with millisecond smoothing (6°/second) — one full
    rotation per minute (tourbillon cage, seconds hands)."""
    return f"({seconds_precise()}) * 6"


def clamp(expr: str, lo: float | int, hi: float | int) -> str:
    return f"clamp({expr}, {num(lo)}, {num(hi)})"


def ratio(expr: str, lo: float | int, hi: float | int) -> str:
    """Clamped 0..1 normalization of a data source over [lo, hi].

    General form: (clamp(expr, lo, hi) - lo) / (hi - lo).
    Zero-based fast path: when lo == 0 the algebraically identical short
    form clamp(expr, 0, hi) / hi is emitted (this is also the exact
    device-proven Aurelius battery expression).
    Rejects hi <= lo.
    """
    if float(hi) <= float(lo):
        raise ValueError(f"ratio(): hi ({hi}) must be greater than lo ({lo})")
    if float(lo) == 0:
        return f"{clamp(expr, lo, hi)} / {num(hi)}"
    span = hi - lo
    return f"({clamp(expr, lo, hi)} - {num(lo)}) / {num(span)}"


def rotation_continuous(speed_deg_per_sec: float | int,
                        reverse: bool = False) -> str:
    """Continuously rotating element angle at a fixed mechanical speed.

    Forward:  ((elapsed) * speed) % 360
    Reverse:  360 - (((elapsed) * speed) % 360)
    """
    base = f"(({elapsed_seconds()}) * {num(speed_deg_per_sec)}) % 360"
    return f"360 - ({base})" if reverse else base


def parallax_offset(base: float | int, amplitude: float | int,
                    axis: str, max_angle: int = 45) -> str:
    """Accelerometer parallax displacement — the single most shared pattern
    in the ten-face audit (9/10 faces).

    base + amplitude * clamp([ACCELEROMETER_ANGLE_axis], -max, max) / max
    """
    if axis not in ("X", "Y"):
        raise ValueError(f"axis must be X or Y, got {axis!r}")
    src = f"[ACCELEROMETER_ANGLE_{axis}]"
    # A negative amplitude (used to counter-rotate a reactive layer) must not
    # emit "base + -22.0 * ..."; fold the sign into the operator instead.
    op, mag = ("-", -amplitude) if float(amplitude) < 0 else ("+", amplitude)
    return (f"{num(base)} {op} {num(mag)} * "
            f"clamp({src}, -{num(max_angle)}, {num(max_angle)}) / {num(max_angle)}")


def heart_rate_bpm(fallback: int = 70, lo: int = 40, hi: int = 200) -> str:
    """Heart-rate reading with a fallback before a valid value exists and a
    safety clamp. WFF reports 0/low values before the sensor delivers."""
    return f"clamp(([HEART_RATE] < 30 ? {num(fallback)} : [HEART_RATE]), {num(lo)}, {num(hi)})"


def hr_oscillator_angle(center: float | int, amplitude: float | int,
                        rad_per_beat: float | str = 0.10472,
                        fallback: int = 70, lo: int = 40,
                        hi: int = 200) -> str:
    """Balance-wheel oscillation whose frequency tracks live heart rate.

    center + amplitude * sin(elapsed * bpm * rad_per_beat)

    rad_per_beat 0.10472 == 2*pi/60: one full sine cycle per beat.
    """
    return (f"{num(center)} + {num(amplitude)} * "
            f"sin(({elapsed_seconds()}) * "
            f"({heart_rate_bpm(fallback, lo, hi)}) * {num(rad_per_beat)})")


def gauge_angle(start_deg: float | str, sweep_deg: float | str,
                source: str = "[BATTERY_PERCENT]",
                lo: int = 0, hi: int = 100) -> str:
    """Data gauge needle: start + sweep * clamp(source, lo, hi) / hi."""
    return f"{num(start_deg)} + {num(sweep_deg)} * {ratio(source, lo, hi)}"


def breathing_alpha(base: float | int, amplitude: float | int,
                    rad_per_sec: float | str) -> str:
    """Slow sinusoidal alpha 'breathing' (sheen/glow layers)."""
    return (f"{num(base)} + {num(amplitude)}*"
            f"sin(({elapsed_seconds()})*{num(rad_per_sec)})")


# ---------------------------------------------------------------------------
# Seamless looping motion
#
# WHY PERIODS MUST DIVIDE 3600. The engine's time base, elapsed_seconds(), is
# seconds *within the hour*: it runs 0 -> 3599.999 and then snaps to 0. A
# scroll built on fract(elapsed / period) is only continuous across that snap
# if the cycle closes exactly at the hour, i.e. if 3600 / period is a whole
# number. Get it wrong and a rain layer jumps once an hour — rare enough to
# survive review and obvious enough to ruin the effect.
#
# SECONDS_SINCE_EPOCH would not wrap, but at ~1.7e9 a 32-bit float resolves to
# about 128-second steps, so fract() of it is worthless. Staying inside the
# hour is the only way to keep millisecond smoothness.
# ---------------------------------------------------------------------------

def _check_period(period_s: float, what: str) -> None:
    if period_s <= 0:
        raise ValueError(f"{what}: period must be positive, got {period_s}")
    cycles = 3600.0 / period_s
    if abs(cycles - round(cycles)) > 1e-9:
        raise ValueError(
            f"{what}: period {period_s}s does not divide the 3600s time base "
            f"({cycles:.6f} cycles per hour), so the loop would jump on the "
            f"hour. Use 3600/n — e.g. 1.0, 1.2, 1.5, 2.0, 2.4, 3.0, 4.0, "
            f"4.5, 5.0, 6.0, 7.2, 8.0, 9.0, 10.0, 12.0.")


def scroll_cycle(period_s: float) -> str:
    """A 0->1 sawtooth completing once every `period_s`, hour-safe.

    This is the loop primitive: multiply it by a texture's tile height to
    scroll that texture seamlessly forever.
    """
    _check_period(period_s, "scroll_cycle")
    return f"fract(({elapsed_seconds()}) / {num(float(period_s))})"


def scroll_offset(distance: float | int, period_s: float,
                  reverse: bool = False) -> str:
    """Seamless scrolling displacement for a vertically tiling texture.

    Returns a *relative* offset in the range [0, distance) (or the negative
    of it), which is what a Gyro/Transform delta wants. `distance` must be
    the texture's tile period in pixels, not the sprite height — scrolling by
    anything else shows the seam.
    """
    cyc = scroll_cycle(period_s)
    return (f"0 - {num(float(distance))} * {cyc}" if reverse
            else f"{num(float(distance))} * {cyc}")


def sway_offset(amplitude: float | int, period_s: float,
                phase: float = 0.0) -> str:
    """Sinusoidal lateral sway — snow drifting, a scene breathing.

    Relative, centred on zero. Hour-safe on the same rule as scroll_offset.
    """
    _check_period(period_s, "sway_offset")
    turns = f"({elapsed_seconds()}) / {num(float(period_s))}"
    if phase:
        turns = f"{turns} + {num(float(phase))}"
    return f"{num(float(amplitude))} * sin(({turns}) * 6.2831853)"


def flash_alpha(peak: int = 255, sharpness: float = 12.0,
                period_s: float = 12.0, floor_alpha: int = 0) -> str:
    """A lightning flash: dark for most of the cycle, briefly very bright.

    Built as peak * (1 - sawtooth)^sharpness. A high power collapses the ramp
    into a spike at the top of each cycle, which reads as a strike rather than
    a pulse. `sharpness` 12 gives roughly a 0.2s flash in a 12s cycle.

    Deliberately NOT rand(): the format's rand(,) re-rolls per evaluation, so
    it flickers at the frame rate instead of striking.
    """
    if not 0 <= peak <= 255 or not 0 <= floor_alpha <= 255:
        raise ValueError("flash_alpha: alphas must be 0..255")
    if sharpness <= 1:
        raise ValueError("flash_alpha: sharpness must exceed 1 to read as a "
                         "strike rather than a throb")
    cyc = scroll_cycle(period_s)
    spike = f"pow(1 - {cyc}, {num(float(sharpness))})"
    span = peak - floor_alpha
    if floor_alpha:
        return f"{num(floor_alpha)} + {num(span)} * {spike}"
    return f"{num(span)} * {spike}"


# ---------------------------------------------------------------------------
# Wrist motion
#
# WFF HAS NO GYROSCOPE, though the format calls this family "gyro" throughout
# (common/transform/gyroElements.xsd, gyroArithmeticExpressionType). What it
# exposes is the accelerometer, in two distinct flavours:
#
#   ACCELEROMETER_ANGLE_X/Y/Z/XY  orientation, in degrees. Well behaved,
#                                 device-proven on the Watch7, and what every
#                                 tilt-reactive layer in this collection uses.
#   ACCELEROMETER_X/Y/Z           raw linear acceleration. This is the only
#                                 source that senses *movement* rather than
#                                 attitude — a jolt, a swing, a knock.
#
# The raw family's units are undocumented in the schema. Android's
# SensorEvent contract reports m/s^2, so rest magnitude is ~9.81, and that is
# the default here — but it is an inference from the platform, not from the
# WFF spec, so anything built on it stays opt-in until it is checked on a
# real wrist.
# ---------------------------------------------------------------------------

TILT_AXES = ("X", "Y", "Z", "XY")
RAW_AXES = ("X", "Y", "Z")


def tilt_shift(amplitude: float | int, axis: str = "X",
               max_angle: int = 45) -> str:
    """Relative wrist-tilt displacement, for a <Gyro> attribute.

    Unlike parallax_offset() this carries no base term. The Gyro element is
    additive against whatever the part already is, so a base would double the
    layer's position. Keep parallax_offset() for Transform targets, which are
    absolute, and use this for Gyro.
    """
    if axis not in TILT_AXES:
        raise ValueError(f"tilt axis must be one of {TILT_AXES}, got {axis!r}")
    if max_angle <= 0:
        raise ValueError("tilt_shift: max_angle must be positive")
    src = f"[ACCELEROMETER_ANGLE_{axis}]"
    # Fold the sign into a leading "0 - ..." rather than emitting "+ -24.0",
    # which the format's operator list has no production for.
    mag = abs(float(amplitude))
    body = (f"{num(mag)} * clamp({src}, -{num(max_angle)}, {num(max_angle)})"
            f" / {num(max_angle)}")
    return f"0 - {body}" if float(amplitude) < 0 else body


def tilt_ratio(axis: str = "XY", max_angle: int = 45) -> str:
    """Wrist tilt as a clamped 0..1 magnitude — how far off level the wrist is.

    ACCELEROMETER_ANGLE_XY is the combined tilt, so this is the natural driver
    for anything that should respond to being moved *at all* regardless of
    direction: glass glare, a settling horizon, rain slant.
    """
    if axis not in TILT_AXES:
        raise ValueError(f"tilt axis must be one of {TILT_AXES}, got {axis!r}")
    return (f"abs(clamp([ACCELEROMETER_ANGLE_{axis}], -{num(max_angle)}, "
            f"{num(max_angle)})) / {num(max_angle)}")


def jolt_ratio(rest_magnitude: float = 9.81, span: float = 6.0) -> str:
    """How hard the watch is being moved right now, as a clamped 0..1.

    sqrt(x^2+y^2+z^2) is total proper acceleration; at rest it equals gravity.
    Subtracting the resting magnitude and taking the absolute value leaves
    only what the wearer is doing to the watch, so this reads a flick or a
    knock and ignores attitude entirely.

    CALIBRATION: `rest_magnitude` assumes the raw sources are m/s^2 per
    Android's SensorEvent contract. The WFF schema documents no units. If a
    device reports in g the resting value is 1.0 instead, and this expression
    saturates permanently — which is why callers keep it opt-in until it has
    been watched on hardware.
    """
    if rest_magnitude <= 0 or span <= 0:
        raise ValueError("jolt_ratio: rest_magnitude and span must be positive")
    mag = ("sqrt([ACCELEROMETER_X] * [ACCELEROMETER_X]"
           " + [ACCELEROMETER_Y] * [ACCELEROMETER_Y]"
           " + [ACCELEROMETER_Z] * [ACCELEROMETER_Z])")
    return (f"clamp(abs({mag} - {num(float(rest_magnitude))}), 0, "
            f"{num(float(span))}) / {num(float(span))}")


def if_accelerometer(expr: str, fallback: str | float | int = 0) -> str:
    """Guard a motion expression behind ACCELEROMETER_IS_SUPPORTED.

    A watch without the sensor reports a constant, and a layer offset by a
    constant is a layer that is simply in the wrong place. Falling back to a
    literal keeps such a device on the neutral pose instead.
    """
    return f"([ACCELEROMETER_IS_SUPPORTED] ? ({expr}) : {num(fallback)})"
