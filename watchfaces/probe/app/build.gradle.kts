plugins {
    id("com.android.application")
}

// MERIDIAN PROBE — phase 0 instrument, development build.
//
// Not a design and not a candidate for release. It exists to be worn while
// WEATHER.CONDITION's integers are written down, and to settle what the
// forecast sources actually return on hardware. Every asset is drawn by
// tools/make_probe_assets.py from seeded arithmetic, so unlike the rest of
// the MERIDIAN line it carries no generated-art provenance debt — but it is
// still debug-signed and .dev namespaced, and there is no release config.
// The first build rendered as a black screen: a watch face that fails to
// inflate shows nothing and says nothing, and this one carried a dozen
// unproven sources at once. So it now builds as a ladder — pass -Pstage=A..E
// and each rung becomes its own package, installable side by side, so the
// last one that renders names the culprit.
val stage: String = (project.findProperty("stage") as String? ?: "E").uppercase()

android {
    namespace = "com.xsytrance.probe.dev"
    compileSdk = 36

    // resValue is off by default in this AGP; the label is the only thing
    // distinguishing the five rungs in the picker, so it has to be on.
    buildFeatures { resValues = true }

    defaultConfig {
        applicationId = "com.xsytrance.probe${stage.lowercase()}.dev"
        minSdk = 34
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-$stage-dev"
        resValue("string", "probe_label", "PROBE $stage")
    }
}
