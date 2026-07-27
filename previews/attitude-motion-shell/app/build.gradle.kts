// ATTITUDE motion PREVIEW shell. PREVIEW ONLY.
// Debug builds only. No release block, no bundle block, and deliberately
// no signing material of any kind.
plugins { id("com.android.application") }

android {
    namespace = "com.xsytrance.attitude.preview"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.xsytrance.attitude.preview"
        minSdk = 33
        targetSdk = 36
        versionCode = 1
        versionName = "0.0.1-preview"
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

    buildTypes {
        debug { isMinifyEnabled = false }
    }
}
