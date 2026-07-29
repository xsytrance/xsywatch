plugins {
    id("com.android.application")
}

// MERIDIAN COMMODORE PRO — development build.
//
// A separate package from MERIDIAN COMMODORE on purpose: the two are meant to
// sit on the wrist together and be compared, which is the only honest way to
// judge whether the layered window is better than the generated one.
//
// The WINDOW here is original by construction — nine procedural layers from
// tools/make_pro_window.py, seeded arithmetic, no model and no prompt. The
// PLATE, hands and instruments are still carried over from COMMODORE and are
// still AI-generated. See PROVENANCE.md. Debug signing, .dev namespace, not
// for submission.
android {
    namespace = "com.xsytrance.commodorepro.dev"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.xsytrance.commodorepro.dev"
        minSdk = 34
        targetSdk = 36
        versionCode = 5
        versionName = "0.5.0-dev"
    }
}
