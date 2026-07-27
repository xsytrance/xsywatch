// DISPOSABLE SPIKE - NOT PRODUCT CODE.
// Debug builds only. No release block, no signing config, no bundle config.
plugins { id("com.android.application") }

android {
    namespace = "com.xsytrance.attitude.spike"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.xsytrance.attitude.spike"
        minSdk = 33
        targetSdk = 36
        versionCode = 1
        versionName = "0.0.1-spike"
    }

    flavorDimensions += "profile"
    productFlavors {
        create("assertive") {
            dimension = "profile"
            applicationIdSuffix = ".assertive"
            versionNameSuffix = "-assertive"
        }
        create("damped") {
            dimension = "profile"
            applicationIdSuffix = ".damped"
            versionNameSuffix = "-damped"
        }
        create("proposed") {
            dimension = "profile"
            applicationIdSuffix = ".proposed"
            versionNameSuffix = "-proposed"
        }
    }

    // Deliberately absent: any signing block, any release buildType
    // customisation, any bundle block. The spike must not be able to
    // produce a signed or releasable artifact, and a gate asserts that
    // none of those tokens appears in this file.
    buildTypes {
        debug { isMinifyEnabled = false }
    }
}
