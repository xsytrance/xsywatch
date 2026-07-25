# Memory-footprint evaluator evidence (google/watchface play-validations 1.7.0)

```
$ java -jar memory-footprint.jar --watch-face <candidate app-debug.apk> --schema-version 4 --ambient-limit-mb 10 --active-limit-mb 100
Test report:
[MEMORY_FOOTPRINT]: ✅PASS✅ Watch Face has passed the memory footprint test. ✅ 

$ java -jar memory-footprint.jar --watch-face releases/aurelius/current/aurelius.apk (immutable Phase-1 release) ...
Test report:
[MEMORY_FOOTPRINT]: ✅PASS✅ Watch Face has passed the memory footprint test. ✅ 
```

Re-run 2026-07-24 (device-evidence session) against the **corrected**
candidate `b01015c87eea…` (post asset-divergence fix, see
`ASSET_DIVERGENCE_FINDING.md`):

```
$ java -jar memory-footprint.jar --watch-face watchfaces/aurelius/app/build/outputs/apk/debug/app-debug.apk --schema-version 4 --ambient-limit-mb 10 --active-limit-mb 100
Test report:
[MEMORY_FOOTPRINT]: ✅PASS✅ Watch Face has passed the memory footprint test. ✅
```
