# rc2 physical Watch7 validation — PARTIALLY BLOCKED

**Status:** **STILL BLOCKED, but no longer for the original reason.**
Not skipped, not waived.

**Superseded claim:** an earlier revision of this document stated that
`adb devices` reported zero attached devices throughout and that nothing
on the physical matrix could proceed. **That is no longer true.** A device
session took place on 2026-07-26 over wireless adb
(`192.168.1.183:45079`, Galaxy Watch7 44 mm SM-L310, Android 16 / API 36)
and closed four rows of the matrix. The original text is preserved in git
history rather than silently rewritten; this revision records what
actually happened.

## What the device session CLOSED

| Row | Result | Evidence |
|---|---|---|
| install through upgrade continuity from the approved package | **PASS** — versionCode 1 → 3, minSdk 34 → 36, `install -r`, no uninstall, no data clear | `INSTALL_AND_LINEAGE.md` |
| pulling the installed APK back and hashing it | **PASS** — byte-identical to the candidate | `INSTALL_AND_LINEAGE.md` |
| verifying packaged resources against repository bytes on the device | **PASS** — 58 byte-identical, 0 drift, 2 explained | `INSTALL_AND_LINEAGE.md` |
| heart-rate permission model on the panel | **PASS** — Variant A receives live HR with no permission declared | `PERMISSION_TEST.md` |

Media captured: `media/normal_on_panel.png`, `media/motion_60s.mp4`,
`media/balance_varA_run1.mp4`, `media/balance_varA_run2.mp4`.

## What is STILL blocked

The Checkpoint B **visual and behavioural matrix** has not been run. No
`DEVICE_TEST_RESULTS.md` exists for rc2, and `device-validated` therefore
has no basis to close:

- normal-mode and AOD rendering at actual scale;
- ten sleep/wake cycles;
- date, reserve gauge, hands, gears, cage and parallax rows;
- confirming Command Satin remains readable at actual scale;
- confirming the reserve ticks are more usable without becoming loud;
- confirming no stripe or unintended ornament entered the face;
- crash/ANR review;
- touch-inertness check;
- **heart-rate tracking after deliberate exertion** — both permission runs
  were taken at rest at ~104 bpm, which proves live data but not that the
  value *tracks*;
- **off-wrist fallback** — the implied rate should collapse to exactly
  70.0 bpm.

Also outstanding, and dependent on this gate: three owner wear sessions
bound to APK
`939d2b44b51557dc7f8598870d32af2f6f9cdb7c30472d17376332cb149012fc`
via `python3 tools/wear_log.py`, covering the required contexts
`office`, `home`, `outdoor`, `low-light`.

## Two gates are held open by this document

`installed-APK-hash-verified` and `installed-resource-lineage-verified`
both carry **complete, passing evidence** — nothing more is needed from
the device for either. They sit at `proposed` rather than `complete`
purely because the gate model makes them depend on `device-validated`,
which the unrun visual matrix keeps blocked. That dependency was left in
place deliberately rather than relaxed to make the count look better; the
reasoning is recorded in the phase report.

## To close this

1. Owner re-pairs the Watch7 over wireless debugging and supplies the
   address (it changes per session; the pairing itself persists).
2. Select AURELIUS in the picker — note One UI deactivates the active face
   on reinstall, which is documented behaviour, not a fault.
3. Run the matrix above and record it in `DEVICE_TEST_RESULTS.md`, which
   must name APK `939d2b44…` explicitly.
4. Record the wear sessions.

**Checkpoint B must not be approved on this evidence being absent.**
