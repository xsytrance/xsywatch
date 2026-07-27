#!/usr/bin/env bash
# Read back the heart rate the AURELIUS face is actually being handed.
#
# The balance wheel oscillates once per heartbeat (HR/60 Hz), so measuring
# its frequency from a screen recording reads back the rate the WFF runtime
# supplied — without the face ever displaying a number. The documented
# fallback is exactly 70.0 bpm = 1.1667 Hz, so a face running on the
# fallback is unambiguously distinguishable from one receiving live data.
#
#   tools/hr_probe.sh <serial> <label> [seconds]
#
#   tools/hr_probe.sh 192.168.1.183:41234 rest
#   tools/hr_probe.sh 192.168.1.183:41234 post_exertion
#   tools/hr_probe.sh 192.168.1.183:41234 off_wrist
#
# The face MUST be the active watch face and on screen: this records the
# panel. The screen timeout is raised for the capture and restored after,
# because the Watch7 sleeps in seconds and a sleeping panel yields a
# zero-byte recording — which is exactly what happened on the first live
# matrix run.
#
# Fail-closed: an empty or unreadable recording is reported as BLOCKED
# rather than producing a number.
set -u

if [ $# -lt 2 ]; then
  echo "usage: $0 <adb-serial> <label> [seconds]" >&2
  echo "  find the serial on the watch: Settings -> Developer options" >&2
  echo "  -> Wireless debugging (IP:port changes every session)" >&2
  exit 2
fi

S="$1"
LABEL="$2"
SECS="${3:-14}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO/docs/reports/evidence/phase-4/aurelius/rc2/hr/$LABEL"

if ! adb -s "$S" shell true >/dev/null 2>&1; then
  echo "BLOCKED: $S is not reachable. Check the watch is on the same" >&2
  echo "         network and re-read the address from Wireless debugging." >&2
  exit 1
fi

mkdir -p "$OUT"
PREV=$(adb -s "$S" shell settings get system screen_off_timeout | tr -d '\r')
adb -s "$S" shell settings put system screen_off_timeout 300000 >/dev/null
adb -s "$S" shell input keyevent KEYCODE_WAKEUP >/dev/null
sleep 1

STATE=$(adb -s "$S" shell dumpsys power | grep -o 'mWakefulness=[A-Za-z]*' | head -1)
adb -s "$S" shell screenrecord --time-limit "$SECS" --size 480x480 \
    /sdcard/hr_probe.mp4
adb -s "$S" pull /sdcard/hr_probe.mp4 "$OUT/recording.mp4" >/dev/null 2>&1
adb -s "$S" shell rm -f /sdcard/hr_probe.mp4 >/dev/null
adb -s "$S" shell settings put system screen_off_timeout "$PREV" >/dev/null

SIZE=$(stat -c%s "$OUT/recording.mp4" 2>/dev/null || echo 0)
if [ "$SIZE" -lt 1000 ]; then
  echo "BLOCKED: recording is ${SIZE} bytes ($STATE) — the panel was asleep"
  echo "         or the recorder never started. No number is reported."
  exit 1
fi

if ! command -v ffmpeg >/dev/null; then
  echo "BLOCKED: recording captured at $OUT/recording.mp4 but ffmpeg is"
  echo "         not installed, so the frequency cannot be measured."
  exit 1
fi

rm -rf "$OUT/frames"; mkdir -p "$OUT/frames"
ffmpeg -y -loglevel error -i "$OUT/recording.mp4" -vf fps=30 \
    "$OUT/frames/f%04d.png"
N=$(find "$OUT/frames" -name '*.png' | wc -l)
echo "label=$LABEL  ${SECS}s  frames=$N  $STATE  (timeout restored to $PREV)"
python3 "$REPO/tools/balance_frequency.py" "$OUT/frames"
# frames are a derived intermediate; the recording is the evidence
rm -rf "$OUT/frames"
echo
echo "fallback is exactly 70.0 bpm = 1.1667 Hz"
echo "recording kept at ${OUT#"$REPO"/}/recording.mp4"
