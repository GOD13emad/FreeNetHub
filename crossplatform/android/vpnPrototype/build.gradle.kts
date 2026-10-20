import java.security.MessageDigest

plugins { id("com.android.application"); kotlin("android") }

android {
    namespace = "com.freenethub.mobile.prototype"
    compileSdk = 36
    buildToolsVersion = "35.0.0"

    defaultConfig {
        applicationId = "com.freenethub.mobile.prototype"
        minSdk = 29
        targetSdk = 36
        versionCode = 2
        versionName = "0.2-private-usb"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
kotlin { jvmToolchain(17) }

dependencies {
    implementation(files("libs/hev-socks5-tunnel-2.18.0.aar"))
}

// Verify native dependency before invoking Android AAR transforms.
val verifyHevNativeArtifact = tasks.register("verifyHevNativeArtifact") {
    doLast {
        val aar = layout.projectDirectory.file("libs/hev-socks5-tunnel-2.18.0.aar").asFile
        check(aar.isFile && aar.length() == 590342L) { "HEV_AAR_MISSING_OR_SIZE_CHANGED" }
        val digest = MessageDigest.getInstance("SHA-256")
        aar.inputStream().use { stream ->
            val buf = ByteArray(32768)
            while (true) {
                val n = stream.read(buf)
                if (n < 0) break
                digest.update(buf, 0, n)
            }
        }
        val actual = digest.digest().joinToString("") { "%02x".format(it) }
        check(actual == "15ec8ed121663b562c99caa5bb602d1009f24e5b09e733438b81988f12feaaab") { "HEV_AAR_SHA256_MISMATCH" }
    }
}
tasks.named("preBuild").configure { dependsOn(verifyHevNativeArtifact) }
