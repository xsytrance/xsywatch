plugins {
    id("com.android.application")
}

// MERIDIAN SQUADRON — ATTITUDE SQUADRON collection, development build.
//
// Debug signing only. No release signing block, no bundle configuration and
// no store metadata. The application ID is namespaced .dev so it can never
// collide with, or be mistaken for, a shipped package.
android {
    namespace = "com.xsytrance.squadron.squadron.dev"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.xsytrance.squadron.squadron.dev"
        minSdk = 34
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-dev"
    }
}
