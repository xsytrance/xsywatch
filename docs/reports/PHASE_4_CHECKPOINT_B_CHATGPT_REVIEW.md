# Phase 4 Checkpoint B — ChatGPT architecture review

**Consumer repository:** `xsytrance/xsywatch`  
**Consumer branch reviewed:** `phase-4/aurelius-release-readiness`  
**Consumer head reviewed:** `67e21d89f226500c34f92b3f59dfeb563dc8b201`  
**Studio repository:** `xsytrance/AGENOR-Horology`  
**Studio branch reviewed:** `phase-4/aurelius-craftsmanship-release-assets`  
**Studio head reviewed:** `2687549c680a01757805443726a484ef8f48e7df`  
**Review date:** 2026-07-26  
**Verdict:** **CHANGES REQUESTED — Checkpoint B is implemented but not accepted; do not merge, promote, sign, upload, or publish**

## Executive assessment

The Phase 4 production work is strong. The studio produced a restrained `CommandSatin_ReservePrecision` finishing generation rather than a redesign; the measured export delta is six changed resources and forty-four byte-identical resources; stable reusable handoff IDs were restored after the attempted generation-specific IDs correctly triggered historical binding failures; the consumer retains zero WFF XML/spec delta; the proposed visual generation and prior approved r2 evidence remain separate; the official WO-P7 luminance gate is materially better than the superseded one-frame lit-pixel heuristic; and the AAB/APK artifacts reproduce byte-for-byte across the reported clean builds.

The central studio and visual-lineage architecture is accepted in principle. Checkpoint B cannot yet be accepted because its canonical Phase 4 contract requires physical Watch7 validation and ordinary release-candidate wear, neither of which exists. The consumer release-candidate layer also has four trust-boundary defects that must be corrected before the candidate is release-grade:

1. the candidate manifest attributes the artifacts to a consumer commit that predates the package/build changes that produced them;
2. the dex-removal task deletes every release dex file without first proving the input contains only generated `R` classes;
3. the API-36 package still declares legacy broad health/activity permissions whose necessity and Play-policy posture are unresolved;
4. candidate validation proves evidence paths exist, but not that required device and wear evidence is complete, passing, and bound to the artifact.

## Accepted findings

- Clean Phase 4 branch boundaries and preserved Phase 1–3 history.
- Immutable historical release `844b9c430f65e0dfaec88604175f1345b4173d647496de4b4ed74359ccfdbcc2` remains untouched.
- Approved r2 normal/AOD/inventory/APK baseline reproduced as reported.
- Owner-selected craftsmanship direction recorded before production import.
- Measured studio object-impact ledger rather than predicted resource scope.
- Exactly six changed runtime assets: `bg`, `bg_aod`, `cage`, `gear_l`, `gear_r`, `hub`.
- Forty-four handoff assets carried forward byte-identically; the explained `balance.png` prediction error is accepted.
- Stable `AureliusMk2_*` asset IDs retained as reusable-slot identities; the rejected `AureliusRc1_*` experiment remains documented.
- Studio producing commit `04015886dbee5cd17b66c4627f822aef3db73d16` is an ancestor of metadata commit `97ba0f1ceeee721a7a2ec0521603bd61935d036d`.
- Zero XML/spec delta and preserved WFF v4 behavior.
- `APPROVAL-0005` correctly remains proposed/pending and supersedes rather than rewrites APPROVAL-0004.
- WO-P7 evidence: 144 ten-minute samples plus sensitivity runs, maximum 3.972% against 15%.
- Candidate AAB/APK hashes, signing states, package identity, WFF validation, memory result, and reported two-build byte equality.
- Removal of the accidental Kotlin runtime from a resource-only face.
- Commercial media/copy separation between Play-compatible screenshots and promotional device-context imagery.
- No production key material and no publication operation.

## Blocker 1 — physical-device and ordinary-wear evidence are absent

The Phase 4 brief defines Checkpoint B as the return point **after implementation and physical validation**, requiring full static, device, and wear evidence. Its acceptance criteria require the owner wear log, full physical-device gate, candidate wear gate, and explicit owner acceptance.

Current state:

- zero wear sessions;
- no Watch7 validation for APK `d02bf91494f94abb5176685baea19b6e788dbd5c92d0df50c4bfde14d00c7956`;
- APPROVAL-0005 owner status remains proposed;
- candidate manifest device status is blocked;
- report body says these items must close before Checkpoint B approval.

Required correction:

1. Change the report headline from “Checkpoint B complete” to **“Checkpoint B implementation complete — acceptance blocked”** until the gates close.
2. Install and validate the exact candidate APK on the Galaxy Watch7 using `qualitative-behavioral-lineage` mode.
3. Pull the installed APK back from the watch and prove its hash equals the candidate hash.
4. Verify the installed runtime-resource byte chain against the rc1 inventory/handoff.
5. Run the complete Phase 4 physical matrix, including r2 comparison, picker/activation, normal/AOD behavior, date, reserve gauge, cage/gears, hands, parallax, touch, stability, sustained motion, and repeated AOD cycles.
6. Record ordinary wear sessions bound to the exact candidate APK. At minimum, the combined evidence must cover:
   - a sustained normal workday;
   - outdoor/daylight and low-light use;
   - sustained AOD;
   - a charging transition;
   - final owner disposition.
7. Preserve honest AOD-panel capture qualifications where the hardware cannot expose ambient pixels.

## Blocker 2 — candidate consumer-source attribution is false

`CANDIDATE.json` records:

```text
consumer_commit = 399ba123bbb13d2272e02764e279a14718e52163
```

That commit implements the WO-P7 gate. The package identity, minSdk change, Kotlin-runtime exclusion, dex-stripping task, AAB build path, artifact verifier, candidate directory, and the AAB/APK themselves were introduced later in `ba4d260c351b594fe6ef07b47447adf65bc8e80c`.

Therefore `399ba12` cannot be the consumer source snapshot that produced the committed artifacts.

Required correction:

1. Establish an explicit consumer lineage analogous to the studio lineage:
   - **consumer source commit** — contains every source, resource, Gradle, manifest, build-script, and verifier input used to build the artifacts, but does not need to contain the resulting candidate manifest;
   - **artifact commit** — contains the canonical AAB/APK and generated VERIFY record;
   - **candidate metadata commit** — contains the final CANDIDATE record and may necessarily be later because a metadata file cannot self-identify its own commit.
2. Build both artifacts twice from clean detached/checkouted copies of the exact consumer source commit.
3. Require both artifact hashes to match across builds.
4. Record all three commit roles and enforce ancestry.
5. Validate that the declared consumer source commit contains every path used by `build_commands`.
6. Reject manifests whose consumer source commit predates any packaging/build input.
7. Add deliberate-failure tests for a stale source commit, non-ancestor artifact/metadata commits, and a build input missing at the declared source commit.

Do not simply change `consumer_commit` to the latest branch head; make the source/artifact/metadata roles explicit and machine-verifiable.

## Blocker 3 — dex stripping is fail-open

`stripRClassDex` recursively deletes every `.dex` under the release dex intermediate. The comments state that the remaining 3 KB dex contains only generated `R` classes, but the task does not inspect its class set before deletion. The final artifact verifier proves the AAB is dex-free; it does not prove what was deleted. It also does not currently report whether the debug APK contains dex.

This creates a dangerous future failure mode: if a real Java/Kotlin class or runtime dependency enters the release graph, the task can silently delete it and still produce a code-free bundle that passes the final no-dex check.

Required correction:

1. Before deletion, inspect every release dex file with an appropriate Android build-tool parser.
2. Allow only class descriptors belonging to generated resource classes for this package, for example `Lcom/xsytrance/aurelius/R;` and `R$*`.
3. Fail the build on any other class before deleting anything.
4. Record the pre-strip dex hashes, sizes, and allowed class descriptors in VERIFY evidence.
5. Verify both final artifacts:
   - AAB contains no dex;
   - debug APK dex state is explicitly reported and matches the intended device-test policy.
6. Add a deliberate-failure fixture that introduces a dummy class or unexpected dependency and proves the build fails rather than silently stripping it.
7. Add a positive fixture for the expected generated-R-only input.

The 77% package-size improvement is accepted; the deletion boundary must become fail-closed.

## Blocker 4 — API-36 health permissions are unresolved and currently stale

The manifest declares:

```xml
<uses-permission android:name="android.permission.BODY_SENSORS" />
<uses-permission android:name="android.permission.ACTIVITY_RECOGNITION" />
```

The package targets API 36. Android 16 / Wear OS 6 migrates heart-rate access from broad `BODY_SENSORS` to granular `android.permission.health.READ_HEART_RATE`; Google Play explicitly advises API-36 apps not to declare broad BODY_SENSORS when a granular permission exists. The face specification uses heart rate for the balance animation and contains no activity/step component that justifies `ACTIVITY_RECOGNITION`.

The repository already identifies this as unresolved, so the current bundle cannot yet support a final Data Safety, Health Apps, or sensitive-permission declaration.

Required correction:

1. Determine empirically and from WFF-specific platform behavior whether the declarative `[HEART_RATE]` source requires the watch-face package itself to declare a permission.
2. Produce controlled candidate builds:
   - no body/activity permission;
   - the minimal API-36 granular heart-rate declaration if required.
3. Test on the physical Watch7 with permission granted, denied, and unavailable; verify live HR behavior and the documented fallback.
4. Remove `ACTIVITY_RECOGNITION` unless a current runtime feature genuinely requires activity data.
5. If the WFF runtime supplies heart rate without package permission, remove both manifest permissions.
6. If package permission is required, use the current granular declaration, complete the Health Apps declaration posture, and ensure the privacy/disclosure material accurately describes ephemeral on-device use.
7. Add validation rejecting unrestricted `BODY_SENSORS` on an API-36 Aurelius build and rejecting unused sensitive permissions.

This must be resolved before the AAB is treated as a release-ready candidate.

## Blocker 5 — evidence validation checks existence, not readiness

The candidate validator currently accepts evidence values when their referenced paths exist. An empty wear directory and a device blocker document therefore satisfy path existence even though the required evidence is absent.

Required correction:

1. Add machine-readable Checkpoint B readiness fields to the candidate manifest, including:
   - device evidence status/result/artifact hash;
   - installed-APK pullback hash;
   - installed-resource lineage result;
   - wear-session count and required-context coverage;
   - owner disposition;
   - owner pixel approval;
   - architecture approval.
2. Validate the content/schema/hashes of the evidence, not only its path.
3. Require the release candidate to remain `blocked` or `proposed` while any required item is missing.
4. Prevent APPROVAL-0005 promotion, golden promotion, lifecycle promotion, or a final-review status of approved until all required evidence is complete and passing.
5. Add deliberate failures for an empty wear directory, a blocker file standing in for device evidence, a session bound to the wrong APK, insufficient context coverage, and a mismatched installed-APK hash.

## Required clarification — candidate-specific artwork provenance

`docs/LICENSING.md` carries a repository-wide warning concerning legacy ComfyUI/SD-family and donor-image work. The current Aurelius rc1 runtime appears to be fully sourced through the AGENOR-Horology Blender pipeline plus audited Rajdhani assets, with forty-four r2 studio assets carried forward and six studio assets updated.

Before treating the generic warning as an Aurelius launch blocker, create a **candidate-specific provenance closure**:

- map all 50 rc1 handoff assets and the generated preview to their actual source classification;
- prove whether any current rc1 runtime pixel derives from an external AI checkpoint or donor image;
- if none do, record the generic legacy warning as **not applicable to Aurelius 2.0.0-rc1** and remove it from this candidate’s open owner actions;
- if any do, identify the exact resource, model/checkpoint, source, hash, and commercial-use terms and resolve them before sale.

Do not erase the repository-wide historical warning; scope it accurately.

## Launch decisions that should not be confused with engineering acceptance

- **TEST-1 account facts:** required to determine launch schedule, but an honestly unresolved account-status field can remain in an unpublished RC manifest. The owner should still supply the four facts before a launch plan is approved.
- **Hosted privacy-policy URL:** required before Play testing/public submission, but the committed privacy-policy text can satisfy the Phase 4 draft-packet requirement until upload is authorized. If health permission remains, hosting/disclosure becomes a more immediate policy prerequisite.
- **Price:** a launch/listing decision, not a static RC-integrity gate. It must be owner-approved before publication, not before the candidate architecture can be reviewed.
- **Support email and response commitment:** required before public listing.

## Visual-review qualification

The connector review verified candidate image paths, hashes, comparison metadata, close-up generation logic, and the reported quantitative deltas. The binary PNGs could not be rendered directly in this review environment. Final judgment of the subtle satin/reserve treatment must therefore come from the owner’s physical-panel wear evidence, which is already a mandatory Checkpoint B gate.

## Required closeout sequence

1. Correct the report/checkpoint status wording.
2. Fix consumer source/artifact/metadata lineage.
3. Make dex stripping fail-closed and verify both AAB/APK dex states.
4. Resolve the API-36 health-permission model on the physical Watch7.
5. Harden candidate evidence validation.
6. Close candidate-specific artwork provenance.
7. Complete physical device evidence and ordinary wear sessions.
8. Record explicit owner pixel/wear acceptance or rejection.
9. Update APPROVAL-0005 and the candidate manifest accurately, without promotion yet.
10. Re-run all engine, visual, aperture, handoff, release, candidate, dex, permission, AOD, build, WFF, memory, repository, whitespace, and CI gates.
11. Return both unmerged branches for final architecture review.

Do not merge either branch. Do not set architecture approval. Do not promote rc1 goldens or asset lifecycles. Do not sign with production material. Do not upload to Play. Do not modify `releases/aurelius/current/`. Do not begin the next product phase.

## Verification boundary

This review inspected branch comparisons, reports, the Phase 4 canonical brief, approval/candidate records, package/Gradle/manifest configuration, build and verifier code, studio handoff history, AOD evidence methodology, and repository policy/provenance records through the GitHub connector. It did not independently execute Blender, Gradle, bundletool, WFF validation, memory evaluation, ADB, or the reported clean builds. Binary close-up images were not directly renderable through the connector environment. Reported local and device results remain subject to the evidence and machine-binding corrections above.
