plugins {
    id("com.android.application")
}

// MERIDIAN COMMODORE — development build.
//
// The dial plate, the ordnance hands and the canopy scene are AI-generated
// concept art. See PROVENANCE.md. Debug signing, .dev namespace, not for
// submission.
android {
    namespace = "com.xsytrance.commodore.dev"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.xsytrance.commodore.dev"
        minSdk = 34
        targetSdk = 36
        versionCode = 2
        versionName = "1.0.0-dev"
    }
}
