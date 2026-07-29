plugins {
    id("com.android.application")
}

// VECTOR PROBE — phase 0 of the MERIDIAN PRO ship plan.
//
// Two rungs, side-by-side installable: -Pstage=A is PartDraw alone, B adds
// the permissionless sources. Debug signing, .dev namespace, an instrument
// not a product. See tools/make_vector_probe.py for what each rung answers.
val stage: String = (project.findProperty("stage") as String? ?: "A").uppercase()

android {
    namespace = "com.xsytrance.vectorprobe.dev"
    compileSdk = 36

    buildFeatures { resValues = true }

    defaultConfig {
        applicationId = "com.xsytrance.vectorprobe${stage.lowercase()}.dev"
        minSdk = 34
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-$stage-dev"
        resValue("string", "probe_label", "VPROBE $stage")
    }
}
