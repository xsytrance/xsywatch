plugins {
    id("com.android.application")
}

// MERIDIAN PURE — development build.
//
// The dial plate, the ordnance hands and the canopy scene are AI-generated
// concept art. See PROVENANCE.md. Debug signing, .dev namespace, not for
// submission.
android {
    namespace = "com.xsytrance.pure.dev"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.xsytrance.pure.dev"
        minSdk = 34
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-dev"
    }
}
