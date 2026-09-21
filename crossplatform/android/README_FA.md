# FreeNet Hub 4.2.0 - Android

- Native framework: `android.net.VpnService`.
- Build gate: **PASS** با JDK 17، Gradle 8.9، compile/target SDK 35 و Build Tools 35.0.0.
- APK پذیرفته‌شدهٔ build-pack: `delivery/FreeNetHub_4.2.0_Android_BuildPack_Debug.apk`.
- package: `com.freenethub.mobile`، versionCode=`420`، versionName=`4.2.0`.
- APK با Android Debug certificate و APK Signature Scheme v2 امضا شده است؛ این امضای production نیست.
- `VpnService` و `BIND_VPN_SERVICE` در manifest وجود دارند.
- packet-forwarding core هنوز لینک نشده است؛ `providerCoreReady=false` و هیچ `Builder.establish()` اجرایی وجود ندارد. بنابراین build success به‌عنوان runtime VPN acceptance گزارش نمی‌شود.
- نبود forwarding core عمداً fail-closed است تا TUN بدون مسیر forwarding ساخته و اینترنت دستگاه blackhole نشود.
- runtime device acceptance و production signing هنوز OPEN هستند.
