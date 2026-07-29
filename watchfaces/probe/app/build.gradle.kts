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
android {
    namespace = "com.xsytrance.probe.dev"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.xsytrance.probe.dev"
        minSdk = 34
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-dev"
    }
}
