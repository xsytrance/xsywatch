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
        versionCode = 3
        versionName = "2.0.0-rc2"
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
// FAIL-CLOSED. The gate inspects every class descriptor each release dex
// DEFINES and deletes only when the complete set is inside the generated-R
// allowlist. Anything else fails the build before packaging.
//
// The previous version deleted every .dex it found and asserted in a
// comment that the content was the R class. That was fail-open: a real
// class or a runtime dependency entering the release graph would have been
// silently deleted, and the bundle would still have passed the final
// "contains no dex" check. Proving the bundle is dex-free says nothing
// about what was removed to make it so.
val stripRClassDex = tasks.register<Exec>("stripRClassDex") {
    val dexDir = layout.buildDirectory.dir("intermediates/dex/release")
    val report = layout.buildDirectory.file("outputs/dex_gate.json")
    val guard = rootProject.file("../../tools/dex_guard.py")
    outputs.upToDateWhen { false }
    commandLine(
        "python3", guard.absolutePath,
        "--dex-dir", dexDir.get().asFile.absolutePath,
        "--package", "com.xsytrance.aurelius",
        "--delete",
        "--report", report.get().asFile.absolutePath,
    )
    // Exec fails the build on a non-zero exit by default; stated explicitly
    // because the whole point of this task is that it must not be skippable.
    isIgnoreExitValue = false
}

tasks.matching { it.name == "packageReleaseBundle" }.configureEach {
    dependsOn(stripRClassDex)
    mustRunAfter(stripRClassDex)
}
tasks.matching { it.name == "mergeDexRelease" }.configureEach {
    finalizedBy(stripRClassDex)
}
