# X1c7 BUSHIDO — build log

A cyberpunk-samurai watch face for the **Samsung Galaxy Watch 7 (44 mm, 480×480)**,
Watch Face Format **v4** (no code), built from the `xsywatch-bushido.jpg` concept.
Owner: xsytrance. Built with Claude Code, 2026-07-21.

Package `com.xsytrance.bushido` · label **X1c7 BUSHIDO** · WFF format version 4
(requires Wear OS 6 / One UI 8 Watch for the ambient-transition reveal; the Watch 7
has this).

## What it is

The samurai on the neon bridge from the concept art is the hero. The mock-up's baked-in
UI is removed (dark HUD gradients + vignette) and a live instrument layer is drawn on top:

- **Big time** 10:08 — hour white, minute magenta, pulsing colon, PM + live seconds.
  Native `DigitalClock`/`TimeText` with the bundled **Chakra Petch** font (crisp, live).
- **Top bar** — samurai-mask logo · `SAT` (day) · `MAY 24` (`[MONTH_S] [DAY]`, uppercased)
  · crescent-moon weather icon + `[WEATHER.TEMPERATURE]°`.
- **X1c7 影の戦士** brand line (pre-rendered kanji plate — no CJK font bundled).
- **Battery** live arc (left rim, `[BATTERY_PERCENT]`) + `100% / BATTERY`.
- **Heart rate** `[HEART_RATE]` with a heart that **flashes on every beat**
  (`abs(sin(t·bpm·π/60))`), `BPM` label, ECG trace.
- **Steps** live `[STEP_COUNT]` + a **step-goal arc** on the top rim (`[STEP_PERCENT]`).
- **Calories / Distance** — tappable `ComplicationSlot`s (SHORT_TEXT). Assign Samsung
  Health "Calories" and "Distance/Exercise" once and they light up + become tap zones.
- **Live atmosphere** — scrolling rain, breathing moon halo, neon glow behind the digits,
  gyro **parallax** (`[ACCELEROMETER_ANGLE_X/Y]`) on the city, scanlines, rim ticks, torii.

## The wrist-raise startup animation

WFF v4 `Variant` transitions (`duration` / `startOffset` / `interpolation`) drive a
**choreographed power-on** every time the watch wakes from ambient:

1. city cross-fades up from the dim AOD ghost,
2. neon glow + digits brighten, colon lights,
3. battery + step arcs sweep/fade in (OVERSHOOT),
4. brand line → top bar → battery/BPM → steps/cal → distance cascade in on staggered
   `startOffset`s,
5. torii **pops in last** with an OVERSHOOT scale.

Ambient (AOD) shows only a dim samurai + dim time + date for battery/burn-in safety.

## Toolchain / pipeline

- `tools/build.py` — single source of truth (layout, palette, fonts). Stages:
  `assets` (PNG art via Pillow) · `xml` (emits `res/raw/watchface.xml`) ·
  `preview` (faithful static render → `res/drawable/preview.png`) · `anim` (reveal GIF).
- `tools/bg.py` — composes the background from the concept art (clean crop, HUD
  darkening of the baked mock-up text, vignette, moon halo) + rain/fog/scan layers.
- Fonts: Chakra Petch (Bold/SemiBold) + Rajdhani (SemiBold/Bold), OFL, in `res/font`.
- Build: `~/gradle 9.6.1` + AGP 9.2.1, JDK = android-studio jbr, `:app:assembleDebug`.

## Validation (no device on the build box)

`watchface.xml` is checked with Google/Samsung's **official WFF validator**
(`third_party/wff/specification/validator`, built offline against the bundled
Xerces XSD-1.1 libs) before every build:

    <scratch>/wffval/run.sh 4 app/src/main/res/raw/watchface.xml   →  ✅ PASSED (v4)

## Hard-won facts

- `<Variant>` is **not** allowed inside `<Arc>` (only Stroke/Transform/Reference) — animate
  arc sweep via `<Transform target="endAngle">`, fade via the parent `<PartDraw>`'s Variant.
- `<DigitalClock>` is not a Part — it takes no `name`/`Variant`/`Transform`. Wrap it in a
  `<Group>` to dim it in ambient and to parallax it.
- `<` inside expression attributes must be `&lt;` or the whole face falls back to system.
- No WFF data source for calories/distance → complication slots.
- `angleType` is `xs:float`, so a progress arc may cross 12 o'clock (start 318 → end 402).

## Regenerating / installing

    python3 tools/build.py all           # assets + xml + preview + reveal gif
    ~/.gradle/.../gradle-9.6.1/bin/gradle :app:assembleDebug   # (JAVA_HOME=jbr)
    adb install -r app/build/outputs/apk/debug/app-debug.apk
    adb shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE \
      --es operation set-watchface --es watchFaceId com.xsytrance.bushido

## 2026-07-22 — FIX: "never installed" was actually "never activated"
Symptom: `adb install` succeeded, but the face never appeared. Root cause was
activation, not install. `am broadcast ... DEBUG_SURFACE set-watchface` failed:

    Broadcast result=2: set-watchface failed. FavoriteOperationException: Error: 0

logcat (WearServices / DeclarativeWatchFaceRuntime) showed the real error:

    IWatchFaceInstanceServiceStub: getUserStyleFlavors failed
    java.lang.IllegalArgumentException:
      defaultDataSourcePolicy.systemDataSourceFallbackDefaultType EMPTY
      must be in the supportedTypes list: [SHORT_TEXT]

Cause: the cal_slot / dist_slot `ComplicationSlot`s had NO `<DefaultProviderPolicy>`.
Without it the runtime defaults the system-fallback type to EMPTY, which isn't in
`supportedTypes=[SHORT_TEXT]`, so metadata fetch throws → add-to-favorites fails →
set-watchface fails. (A plain XSD/validator pass does NOT catch this; it's a
runtime invariant.)

WFF GOTCHA (rule): every ComplicationSlot MUST include a `<DefaultProviderPolicy>`
as its FIRST child, and `defaultSystemProviderType` MUST be one of `supportedTypes`.
Schema (documents/4/complication/defaultProviderPolicyElement.xsd):
  <DefaultProviderPolicy defaultSystemProvider="STEP_COUNT"
                         defaultSystemProviderType="SHORT_TEXT" />
`defaultSystemProvider` enum: APP_SHORTCUT|DATE|DAY_OF_WEEK|FAVORITE_CONTACT|
NEXT_EVENT|STEP_COUNT|SUNRISE_SUNSET|TIME_AND_DATE|UNREAD_NOTIFICATION_COUNT|
WATCH_BATTERY|WORLD_CLOCK|DAY_AND_DATE|EMPTY|HEART_RATE.

Fix applied to both `tools/build.py` (source of truth) and
`app/src/main/res/raw/watchface.xml`: added the DefaultProviderPolicy line
(STEP_COUNT / SHORT_TEXT fallback) to cal_slot and dist_slot.

No gradle/wrapper on this box, so the APK was patched in place: replaced the
uncompiled `res/raw/watchface.xml` entry, zipalign -f -p 4, re-signed with the
debug keystore (same key → installs as update). Result: activation returned
`result=1 Favorite Id=[8]`; runtime rendered com.xsytrance.bushido;
current = X1c7 BUSHIDO. LIVE on the Watch7.
