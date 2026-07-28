# ATTITUDE SQUADRON — Fast Structural Review

**Repository:** `xsytrance/xsywatch`  
**Branch:** `collection/attitude-squadron`  
**Consumer implementation reviewed:** `5689e74463489d868d112dd178483a54474ad02e`  
**Studio head reviewed:** `xsytrance/AGENOR-Horology` `phase-3/attitude-squadron-collection` at `c7f30eb39de61319a488a1bad1b564f031a20446`  
**Verdict:** **CREATIVE AND ARCHITECTURAL DIRECTION ACCEPTED; ONE FINAL-STUDIO LINEAGE REBUILD REQUIRED BEFORE OWNER WRIST PACK**

## Accepted

The overnight sprint delivered a real collection rather than concepts:

- twelve public development faces plus one internal build;
- unique package IDs for every face;
- public branding excludes AGENOR;
- one shared architecture and one shared motion/data contract;
- original procedural artwork;
- sculpted propeller hour/minute hands as the collection signature;
- spinner-style pinion hubs;
- wooden laminated propellers on HERITAGE and BALSA;
- live date, battery, steps and heart-rate bindings;
- separate AOD compositions and frozen AOD horizon;
- APK identities recorded for all thirteen;
- no AAB, production signing, store state, merge, Aurelius change, spike change or automatic installation.

The propeller-hand design direction is accepted. The asymmetric paddle planform, hard camber split, lume spine, tip warning band and opposed counterweight are materially closer to recognizable propeller hardware than generic aviation-themed hands.

## One blocking lineage defect

The consumer collection record and `watchfaces/SQUADRON_IMPORT.json` bind the imported assets to studio commit:

`ca7b6395ded0373f881346187c6dbe6d3f30a1a2`

The submitted final studio head is:

`c7f30eb39de61319a488a1bad1b564f031a20446`

The final studio commits changed every normal/AOD plate to eliminate the alpha-254 aperture-rim ring and regenerated the review sheets and hashes. Therefore the currently recorded consumer import is not bound to the final studio asset authority named in the handoff.

This is not a creative rejection. The difference is visually tiny, but the consumer APKs must either contain the final corrected plate bytes or accurately declare that they were built from the prior studio state. The submitted report claims the final corrected state, so the consumer repository must be refreshed from `c7f30eb...`.

The current `tools/squadron_scaffold.py --check` is also incomplete: it compares only `variants` and does not fail when `studio_commit`, `studio_manifest_sha256`, `platform`, collection metadata, or public-variant metadata differ. This allowed the stale lineage to pass.

## Required fast correction

Perform one mechanical pass only:

1. Pull studio branch `phase-3/attitude-squadron-collection` and verify exact head `c7f30eb39de61319a488a1bad1b564f031a20446`.
2. Re-run the collection scaffold/import from that exact studio checkout.
3. Regenerate all thirteen watchface XML files and all review sheets.
4. Clean-build all thirteen APKs.
5. Update `watchfaces/SQUADRON_IMPORT.json` and `collection/SQUADRON_BUILD_RECORD.json` with the final studio commit, final manifest hash, final asset hashes, final APK hashes and sizes.
6. Strengthen `tools/squadron_scaffold.py --check` to compare the complete authoritative import document, including:
   - schema;
   - collection and flagship;
   - public variants;
   - studio repository, branch and commit;
   - studio manifest SHA-256;
   - platform;
   - all variant metadata and resource hashes.
7. Add regression tests proving a stale studio commit, stale manifest hash, stale platform and stale asset each fail.
8. Re-run the reported gates.

Do not redesign the collection during this correction.

## Owner wrist pack after correction

After the final-studio rebuild succeeds, send the exact existing APKs for:

1. `MERIDIAN HAYATE` — flagship prop-fighter identity;
2. `MERIDIAN COMMODORE` — luxury/commercial direction;
3. `MERIDIAN PURE` — clean public baseline;
4. `MERIDIAN BALSA` — most distinctive wooden-prop/toy-glider direction.

All four may coexist because their package IDs are distinct. Provide full SHA-256 values and byte counts from the corrected build record. Do not require the owner to install all thirteen.

## Boundaries

This correction does not authorize:

- merging to main;
- owner pixel approval for any variant;
- final motion-profile selection;
- AAB or production signing;
- store preparation or publication;
- modification of Aurelius, the spike, or the original MERIDIAN development face.
