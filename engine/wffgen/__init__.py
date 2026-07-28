"""wffgen — the AGENOR build-time WFF engine (ADR-008).

Deterministically generates and validates Watch Face Format XML from
data-driven face specifications. Python standard library only.

This is NOT a runtime Android library: WFF packages are declarative,
resource-only apps; reuse happens at build time by generating the committed
`watchface.xml` from an authoritative spec (`tools/generate_face.py`).

Modules:
    model        deterministic XML element model + serializer
    expressions  WFF arithmetic-expression builders (time, data, motion)
    profiles     ambient (AOD) policies, motion classes, transitions
    components   reusable scene-component factories (behavior, not art)
    render       face spec -> WatchFace document
    validation   structural validation of generated documents
    spec         TOML face-spec loading + component registry

Versioning: the engine is experimental; every generated file embeds
ENGINE_VERSION so drift between engine and committed XML is detectable.
"""

ENGINE_VERSION = "0.1.0-experimental"

# WFF data-source tokens the engine knows how to validate. Extend only with
# tokens documented for WFF v4.
KNOWN_SOURCES = frozenset({
    "MILLISECOND", "SECOND", "MINUTE", "HOUR_0_11", "HOUR_0_23",
    "DAY", "DAY_OF_WEEK_S", "MONTH_S", "AMPM_STRING",
    "BATTERY_PERCENT", "HEART_RATE", "STEP_COUNT", "STEP_PERCENT",
    "ACCELEROMETER_ANGLE_X", "ACCELEROMETER_ANGLE_Y",
    # Weather. These are native WFF v4 sources — no complication provider and
    # no companion app is required, contrary to what this engine previously
    # implied by omitting them. See common/simpleTypes/sourceType.xsd,
    # weatherSourceType.
    "WEATHER.IS_AVAILABLE", "WEATHER.IS_ERROR", "WEATHER.IS_DAY",
    "WEATHER.CONDITION", "WEATHER.CONDITION_NAME",
    "WEATHER.TEMPERATURE", "WEATHER.TEMPERATURE_UNIT",
    "WEATHER.TEMPERATURE_LOW", "WEATHER.TEMPERATURE_HIGH",
    "WEATHER.CHANCE_OF_PRECIPITATION", "WEATHER.UV_INDEX",
})
