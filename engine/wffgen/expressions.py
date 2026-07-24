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
    """Clamped 0..1 ratio of a data source over [lo, hi]."""
    return f"{clamp(expr, lo, hi)} / {num(hi)}"


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
    return (f"{num(base)} + {num(amplitude)} * "
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
