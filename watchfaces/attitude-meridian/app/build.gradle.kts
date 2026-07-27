plugins {
    id("com.android.application")
}

// ATTITUDE — MERIDIAN, development build.
//
// Debug signing only. No release signing block, no bundle configuration, no
// store metadata. The application ID is namespaced under .dev precisely so
// this can never collide with, or be mistaken for, a release package.
android {
    namespace = "com.xsytrance.attitude.meridian.dev"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.xsytrance.attitude.meridian.dev"
        minSdk = 34
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-dev"
    }
}
