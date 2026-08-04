plugins {
    id("com.android.application")
}

// MERIDIAN HOG-WILD — A-10 Warthog, development build.
//
// The dial plate is AI-generated concept art and is DELIBERATELY NOT
// COMMITTED. This package exists to put the design on a wrist for judgement;
// anything that ships is rebuilt as original construction per
// docs/reports/AIRCRAFT_WATCH_DISCOVERY.md.
android {
    namespace = "com.xsytrance.hogwild.dev"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.xsytrance.hogwild.dev"
        minSdk = 34
        targetSdk = 36
        versionCode = 9
        versionName = "1.3.2-dev"
    }
}
