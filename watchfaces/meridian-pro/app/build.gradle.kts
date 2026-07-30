plugins {
    id("com.android.application")
}

// MERIDIAN PRO — the redesign, built to be sold. Base art is a procedural
// layout finished by Kontext Pro over our own render (see PROVENANCE.md);
// instruments and readouts are live WFF vectors and text. Dev build:
// debug signing, .dev namespace. The production identity lands with the
// release phase of docs/plans/MERIDIAN_PRO_SHIP_PLAN.md.
android {
    namespace = "com.xsytrance.meridianpro.dev"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.xsytrance.meridianpro.dev"
        minSdk = 34
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-dev"
    }
}
