# Claude Assignment — ATTITUDE SQUADRON Final-Studio Reimport

Read first:

`docs/reports/ATTITUDE_SQUADRON_FAST_REVIEW.md`

This is a narrow mechanical correction. Do not redesign the collection and do not begin release work.

## Source heads

Consumer branch before this instruction:

`collection/attitude-squadron`

Studio source branch:

`phase-3/attitude-squadron-collection`

Required exact studio head:

`c7f30eb39de61319a488a1bad1b564f031a20446`

The current consumer import is bound to `ca7b6395...`, which predates the final aperture-rim hardening. Refresh the consumer family from the exact final studio head.

## Execute

1. Pull both branches and verify the exact studio head above.
2. Record the current thirteen APK hashes and sizes as the pre-refresh set.
3. Run `tools/squadron_scaffold.py` against the exact final studio checkout.
4. Regenerate XML and review images for all thirteen faces.
5. Clean-build all thirteen APKs.
6. Update the authoritative import and build records with the actual final values.
7. Strengthen `tools/squadron_scaffold.py --check` so it compares the complete import document, not only `variants`.
8. Add behavioral regressions for stale:
   - studio commit;
   - studio manifest hash;
   - platform;
   - public-variant metadata;
   - individual resource hash.
9. Run all engine, visual, collection, WFF and repository-validation gates.
10. Confirm the final normal/AOD plate resources match the final studio manifest and the aperture coverage gate reports zero uncovered pixels for all thirteen.

## Deliver only the four-face wrist pack

After all checks pass, send the owner these exact final APKs:

- MERIDIAN HAYATE;
- MERIDIAN COMMODORE;
- MERIDIAN PURE;
- MERIDIAN BALSA.

Provide package ID, exact SHA-256 and byte count for each. Do not send the internal AGENOR build unless separately requested.

## Stop conditions and boundaries

Do not:

- ask design questions;
- redesign any face;
- change the propeller-hand concept;
- alter the shared scene graph or motion profile;
- merge to main;
- create an AAB, production signing, store metadata or release candidate;
- modify Aurelius, the disposable spike, preview shells or the original ATTITUDE MERIDIAN development face;
- install or contact the Watch7.

Commit and push the corrected consumer branch, send the four exact APKs, report the new head and final hashes, then stop for owner wrist review.
