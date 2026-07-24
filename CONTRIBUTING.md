# Contributing

## Ground rules

- **Read `docs/CHATGPT_ARCHITECT.md` first.** It is the authoritative
  architecture ledger; work that contradicts it needs a documented reason and
  an ADR in `docs/decisions/`.
- **Source is authoritative; APKs are derived** (ADR-002). Never "fix" a face
  by editing a binary or committing a rebuilt APK without the source change
  that produced it.
- No secrets: keystores, tokens, and `local.properties` are git-ignored and
  must stay out of history.

## Branch & commit conventions

- Branches: `phase-N/<topic>`, `face/<slug>/<topic>`, or `fix/<topic>`.
- Commits: imperative subject, scoped where useful —
  `face(bushido): retune AOD ember brightness`, `tools: fail build_all on first error`.
- Logical, reviewable commits. No force-pushes to shared branches.

## Face project contract

Every directory under `watchfaces/<slug>/` is a self-contained Gradle project:

```
watchfaces/<slug>/
├── settings.gradle.kts / build.gradle.kts
├── gradlew, gradle/wrapper/          # committed — builds must not need a global gradle
├── app/
│   ├── build.gradle.kts              # applicationId com.xsytrance.<id>, versionCode/Name
│   └── src/main/
│       ├── AndroidManifest.xml
│       └── res/raw/watchface.xml     # WFF v4 — the face itself
│       └── res/drawable*/            # layer art, preview.png
├── tools/                            # python asset-generation scripts (repo-relative paths)
└── README.md                         # what it is, how to build/install/validate, asset provenance
```

Package IDs are stable identity — never change one on an installed face
without a documented migration reason.

## Quality gates before merging

1. `python3 tools/validate.py` passes (or newly-reported issues are
   explicitly acknowledged in the PR/commit message).
2. The affected face builds: `tools/build_face.sh <slug>`.
3. WFF XML validated (see `docs/BUILD_AND_RELEASE.md`).
4. Visual gates from ledger §11 for anything user-visible: readability,
   no boundary clipping, AOD behavior, preview matches build.
5. `git diff --check` clean; no generated `build/` output staged.

## Releases

Follow `docs/BUILD_AND_RELEASE.md`. Short version: bump versionCode/Name,
build, checksum, update `releases/<slug>/` + `releases/MANIFEST.json`,
changelog entry, device-install sanity test.
