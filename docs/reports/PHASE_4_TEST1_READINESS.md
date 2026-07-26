# TEST-1 — Play Console account status and testing readiness

**Status:** **UNRESOLVED — awaiting owner-supplied facts. Not guessed.**

## What is unresolved

Google Play requires new **personal** developer accounts created after
**2023-11-13** to run a closed test with **at least 12 testers opted in
continuously for 14 days** before production access can even be requested.
Organisation accounts are not subject to it.

> "At least 12 testers must be opted-in to your closed test when you apply
> for production access. They must have been opted-in for the last 14 days
> continuously."
>
> — <https://support.google.com/googleplay/android-developer/answer/14151465>, checked 2026-07-26

Whether this applies to AGENOR is a fact only the owner can supply. The
repository has no evidence of it, and inventing an answer would put a
14-day calendar gate either wrongly on or wrongly off the launch plan.

## What AGENOR needs to provide

1. **Account type** — personal or organisation?
2. **Approximate creation date** — before or after 2023-11-13?
3. **Is Test and release → Production currently accessible** in Play
   Console?
4. **Has a previous app already received production access** on this
   account?

Found in Play Console under *Settings → Developer account → Account
details*, and on the *Dashboard*.

## What has been prepared regardless

Nothing below requires the answer, and none of it creates a public
listing, a real closed test, or a launch calendar.

| Item | State |
|---|---|
| Distribution artifact | ✅ `aurelius-2.0.0-rc1.aab`, reproducible, verified |
| Device-test artifact | ✅ `aurelius-2.0.0-rc1-debug.apk`, debug-signed |
| Listing copy | ✅ draft, `docs/commercial/aurelius/2.0.0-rc1/COPY_DRAFT.md` |
| Play-compatible media | ✅ `docs/commercial/aurelius/2.0.0-rc1/media/play/` |
| Data safety answers | ✅ drafted, pending final-bundle verification |
| Privacy policy text | ✅ drafted — ⚠️ still needs hosting at a public URL |
| Signing plan | ✅ `docs/reports/PHASE_4_SIGNING_PLAN.md`; no key created |

## Contingency: the twelve-tester plan, if the rule applies

Proposed only. Do not start recruiting or open a test track without an
explicit owner instruction.

### Shape

- **14 consecutive days minimum**, and the count is of testers *opted in*,
  not installs. Someone who opts in, tests, and opts out does not count,
  and the 14 days must be consecutive — so recruit everyone **before**
  starting the clock, not during.
- Target **15–16 testers**, not 12. Attrition is the obvious failure mode
  and there is no partial credit.
- Testers need a **Wear OS 6 (API 36)** device. This is the real
  constraint: minSdk 36 means a tester on an older watch cannot install at
  all. Recruit for the device first and the person second.

### Sequence

1. Owner confirms account type and production-access state.
2. If the rule applies: assemble the tester list and confirm each one has
   a compatible watch **before** creating the track.
3. Create a **closed** test track and upload the signed bundle.
4. All testers opt in on day 0.
5. Hold 14 consecutive days. Track opt-ins weekly; replace anyone who
   drops out early enough that the replacement still reaches 14 days.
6. Collect feedback — the owner wear log is the natural instrument, and
   `tools/wear_log.py` already records sessions bound to an exact APK hash.
7. Apply for production access.

### What this does not change

The closed-test requirement gates **publication**, not the craftsmanship
work or the release candidate. It is a calendar constraint on the launch,
and it is the single largest unknown in the schedule.
