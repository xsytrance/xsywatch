"""Ambient (AOD) policies, motion classes, and transition configuration.

Every engine component must declare a motion class (ledger §8) and an AOD
policy — validation refuses undeclared components. Policies serialize to WFF
`Variant mode="AMBIENT"` elements with explicit transition timing.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .model import Elem


class MotionClass(Enum):
    TIME_CRITICAL = "time-critical"        # hour/minute/seconds, indicators
    MECHANICAL = "mechanically-coupled"    # gears, cages, linked assemblies
    AMBIENT_MOTION = "ambient"             # pulses, sheen, parallax
    EVENT = "event"                        # wake transitions, state changes
    STATIC = "static"                      # non-moving layers


@dataclass(frozen=True)
class AmbientPolicy:
    """What a layer does in always-on (ambient) mode.

    ambient_alpha: 0 hides the layer in AOD; 255 keeps it fully lit;
                   intermediate values dim it. AOD discipline: prefer <=140
                   for decorative layers (ledger AOD guidance).
    duration/start_offset: staged transition timing in seconds.
    """
    ambient_alpha: int
    duration: float = 0.4
    start_offset: float = 0.0
    interpolation: str = "LINEAR"

    def __post_init__(self) -> None:
        if not 0 <= self.ambient_alpha <= 255:
            raise ValueError(f"ambient_alpha {self.ambient_alpha} outside 0..255")
        if self.interpolation not in ("LINEAR", "EASE_IN", "EASE_OUT",
                                      "EASE_IN_OUT"):
            raise ValueError(f"unknown interpolation {self.interpolation!r}")

    def variant(self) -> Elem:
        return Elem("Variant", {
            "mode": "AMBIENT", "target": "alpha",
            "value": str(self.ambient_alpha),
            "duration": _f(self.duration),
            "startOffset": _f(self.start_offset),
            "interpolation": self.interpolation,
        })


def _f(v: float) -> str:
    """Timing values render as short decimals: 0.4, 0.16, 0.0 -> '0.0'."""
    s = repr(float(v))
    return s


# Named policies proven by the Aurelius baseline; reusable defaults.
HIDE_IN_AOD = AmbientPolicy(0, duration=0.6, start_offset=0.0,
                            interpolation="EASE_OUT")
REVEAL_IN_AOD = AmbientPolicy(255, duration=0.6, start_offset=0.0,
                              interpolation="EASE_IN")


def dim(alpha: int, duration: float = 0.4, start_offset: float = 0.0,
        interpolation: str = "LINEAR") -> AmbientPolicy:
    """Dim to a specific ambient alpha with staged timing."""
    return AmbientPolicy(alpha, duration, start_offset, interpolation)
