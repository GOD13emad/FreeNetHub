plugins { id("com.android.application"); kotlin("android") }
android {
    namespace="com.freenethub.mobile"; compileSdk=35; buildToolsVersion="35.0.0"
    defaultConfig { applicationId="com.freenethub.mobile"; minSdk=26; targetSdk=35; versionCode=420; versionName="4.2.0" }
    compileOptions {
        sourceCompatibility=JavaVersion.VERSION_17
        targetCompatibility=JavaVersion.VERSION_17
    }
}
kotlin { jvmToolchain(17) }
