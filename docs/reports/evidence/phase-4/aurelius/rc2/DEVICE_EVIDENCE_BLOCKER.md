# rc2 physical Watch7 validation — BLOCKED

**Status:** **BLOCKED — no device reachable.** Not skipped, not waived.

`adb devices` reported zero attached devices throughout this session. The
Galaxy Watch7 connects over wireless debugging, which requires the owner
to pair the watch and supply the connection.

This is the same class of blocker as the Phase-2 device gap, and it was
closed the same way: an owner pairing session.

## What is blocked

Everything in the Checkpoint B physical matrix, including:

- install through upgrade continuity from the approved r2 package;
- pulling the installed APK back and hashing it;
- verifying packaged XML and runtime resources against repository bytes on
  the device;
- normal-mode and AOD rendering at actual scale;
- ten sleep/wake cycles;
- date, reserve gauge, heart-rate fallback, hands, gears, cage, balance,
  parallax;
- confirming Command Satin remains readable at actual scale;
- confirming the reserve ticks are more usable without becoming loud;
- confirming no stripe or unintended ornament entered the face;
- 60 seconds of motion evidence;
- crash/ANR review;
- touch-inertness check.

## What is NOT blocked, and was done

The byte-lineage half of the `qualitative-behavioral-lineage` policy does
not need a device and is complete:

`studio source → producing commit 04015886 → metadata commit 97ba0f1 →
handoff manifest sha → imported resource → inventory 1ec66797 → packaged
APK/AAB`

- 50 exports verified against the producing-commit snapshot by the
  hardened importer;
- the packaged `res/raw/watchface.xml` inside **both** the APK and the AAB
  is byte-identical to the repository copy (`6278f26c…`);
- WFF validator PASS (v4) against the XML extracted from the APK;
- memory-footprint evaluator PASS;
- WO-P7 average-luminance gate PASS at 3.972% of the 15% limit.

## To close this

1. Owner pairs the Watch7 over wireless debugging.
2. `adb install -r releases/aurelius/candidates/2.0.0-rc2/aurelius-2.0.0-rc2-debug.apk`

   Note One UI deactivates the active face on reinstall — documented
   behaviour, not a fault.
3. Run the matrix above and record results here.
4. Record wear sessions against the rc1 APK hash
   `939d2b44b51557dc7f8598870d32af2f6f9cdb7c30472d17376332cb149012fc`
   using `python3 tools/wear_log.py`.

**Checkpoint B must not be approved on this evidence being absent.**
