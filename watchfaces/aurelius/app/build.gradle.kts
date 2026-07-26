plugins { id("com.android.application") }

android {
    namespace = "com.xsytrance.aurelius"
    compileSdk = 36
    defaultConfig {
        applicationId = "com.xsytrance.aurelius"
        // WFF v4 requires Wear OS 6 / API 36
        // (developer.android.com/training/wearables/wff, checked 2026-07-26).
        // minSdk was 34, which allowed installs on devices that cannot
        // render the declared format.
        minSdk = 36
        targetSdk = 36
        versionCode = 2
        versionName = "2.0.0-rc1"
    }
    // A declarative watch face has no code: AndroidManifest declares
    // android:hasCode="false" and there is not one .java or .kt source.
    // Play rejects a Watch Face Format bundle containing dex ("Watch face
    // with minSdk >= 33 cannot have dex files"), and AGP was packaging the
    // Kotlin runtime — 2.4 MB of classes.dex nothing can ever call.
    buildFeatures {
        buildConfig = false
        resValues = false
        shaders = false
    }
}

// Drop the implicitly-added Kotlin runtime so no dex is generated at all.
// The build script being .kts is a build-time concern; it does not require
// a runtime library inside the shipped artifact.
//
// Scoped to the RUNTIME CLASSPATH deliberately. Excluding Kotlin from every
// configuration also strips it from Lint's own tooling classpath, and
// lintVitalAnalyzeRelease then dies on kotlin/enums/EnumEntriesKt. Only
// what gets packaged is filtered.
configurations.matching { it.name.endsWith("RuntimeClasspath") }
    .configureEach {
        exclude(group = "org.jetbrains.kotlin")
        exclude(group = "org.jetbrains", module = "annotations")
    }

// Excluding Kotlin removes 2.4 MB of dex but not the last 3 KB: AGP always
// generates and dexes the resource R class, and bundletool then refuses the
// bundle outright ("Watch face with minSdk >= 33 cannot have dex files").
// android.nonTransitiveRClass and android.enableAppCompileTimeRClass were
// both tried and neither suppresses it.
//
// The R class is unreachable by construction — AndroidManifest declares
// android:hasCode="false", so the platform never loads a class loader for
// this package, and there is no code to reference R with. Dropping the dex
// before the bundle is packaged is therefore semantically inert, and it is
// the difference between having a distributable artifact and not having one.
//
// tools/verify_candidate.py re-checks, on the produced artifacts, that the
// only thing ever dexed was the R class and that neither the bundle nor the
// APK contains dex.
val stripRClassDex = tasks.register("stripRClassDex") {
    val dexDir = layout.buildDirectory.dir("intermediates/dex/release")
    outputs.upToDateWhen { false }
    doLast {
        val root = dexDir.get().asFile
        if (root.exists()) {
            root.walkTopDown()
                .filter { it.isFile && it.extension == "dex" }
                .forEach {
                    logger.lifecycle("stripRClassDex: removing ${it.name} " +
                                     "(${it.length()} bytes, R class only)")
                    it.delete()
                }
        }
    }
}

tasks.matching { it.name == "packageReleaseBundle" }.configureEach {
    dependsOn(stripRClassDex)
    mustRunAfter(stripRClassDex)
}
tasks.matching { it.name == "mergeDexRelease" }.configureEach {
    finalizedBy(stripRClassDex)
}
