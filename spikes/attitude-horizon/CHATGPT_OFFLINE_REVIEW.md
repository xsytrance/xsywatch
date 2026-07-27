# ATTITUDE Horizon Spike — ChatGPT Offline Review

**Repository:** `xsytrance/xsywatch`  
**Branch:** `spike/attitude-horizon-watch7`  
**Commit reviewed:** `fce42aabcd0f7391b105175cfb08f1d2fe967349`  
**Base:** `3333d427e9c87f1c59b26d61c41f6b9ce6435152`  
**Verdict:** **OFFLINE SPIKE BUILD ACCEPTED; DEVICE SESSION NOT YET READY; CAPTURE/ANALYSIS ORCHESTRATION REQUIRED**

## Accepted

The spike respects the authorized experiment boundary:

- it is one commit from the clean accepted consumer baseline, not from the Aurelius Phase 4 working branch;
- all changed paths are confined to the spike plus a dedicated ignore rule;
- it creates three distinct application IDs and debug-only variants;
- the Android manifest declares no permissions and contains no code component;
- there is no release build type, signing configuration, bundle/AAB output, store state or release candidate;
- WFF4 XML uses clamped accelerometer angle expressions;
- DAMPED, PROPOSED and ASSERTIVE have distinct gains and positive conservative coverage margins;
- AOD sets angle and vertical position to constants rather than preserving live expressions;
- the artwork is deliberately crude and separate from production ATTITUDE assets;
- implementation is spike-local and does not modify the shared WFF engine;
- build and source manifests record package IDs, hashes, sizes, margins and disposable status;
- owner observations are fail-closed and remain PENDING;
- no installation or device evidence is claimed.

The reported APK identities are internally consistent with `BUILD_RECORD.json`:

- damped: `com.xsytrance.attitude.spike.damped`
- proposed: `com.xsytrance.attitude.spike.proposed`
- assertive: `com.xsytrance.attitude.spike.assertive`

No remote CI/status check is attached to the reviewed commit, so the reported local test and reproducibility totals are accepted as submitted rather than independently reproduced by this connector.

## Device-harness readiness gap

`device_harness.py` contains useful analysis primitives and a sound fail-closed plan, but its executable path does not yet perform a capture or an analysis:

- without `--run`, it prints/writes the plan;
- with `--run`, it verifies the serial and APK, prints a manual install command, and exits;
- there is no capture subcommand invoking `screenrecord`, `screencap`, sleep/wake cycles, logcat collection or installed-APK pullback;
- there is no frame-extraction path for recordings;
- there is no CLI path feeding captured frames into `horizon_line`, `rest_stability`, `sweep_behaviour` or `mask_edge_exposure`;
- there is no generated evidence record binding the analysis output to the required device and APK fields.

This is an implementation-readiness gap, not a defect in the three APKs. The device session must not start until the harness can actually execute the prepared protocol after an explicit owner action.

## Required harness patch before installation

Keep installation manual and owner-initiated. Add explicit, separately invoked operations such as:

- `--verify-installed` to resolve package path, pull the installed APK and compare SHA-256;
- `--capture <capture-id>` to execute one named capture only;
- `--extract-frames` for recorded motion evidence using a declared deterministic method/tool;
- `--analyze <capture-id>` to run the existing raw, unsmoothed measurements;
- `--finalize` to emit a fail-closed device result bound to variant, source commit, built hash, pullback hash, model, API and timestamp.

The harness must refuse analysis when any required binding is missing. Raw captures must be preserved; derived frames and metrics must identify their source hashes. It must remain impossible to auto-install merely by invoking the harness.

Add deliberate-failure tests for:

- missing installed pullback hash;
- built/pullback hash mismatch;
- wrong package for selected variant;
- missing device identity or API;
- missing capture file;
- too few measurable frames;
- an AOD series that moves;
- analysis output not bound to raw-capture hashes.

## Current authorization

- Preserve the three debug APK builds.
- Patch the harness and offline evidence schema.
- Do not install yet.
- Do not begin production ATTITUDE implementation.
- Do not modify Aurelius, the shared engine, signing, release or store state.
- SEXTANT remains provisional until pixel review and device interaction results are both complete.
