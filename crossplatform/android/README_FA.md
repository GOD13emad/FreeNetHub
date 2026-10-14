# FreeNet Hub 4.2.0 — Android (Fail-Closed Prototype)

- Package: `com.freenethub.mobile`; versionCode `420`, versionName `4.2.0`.
- Current source toolchain: JDK 17, Gradle 8.11.1 (hosted CI), Android Gradle Plugin 8.10.1, compile/target SDK 36 and Build Tools 35.0.0.
- `FreeNetVpnService.kt` is retained as an **unlinked source stub only**: `providerCoreReady() = false` and no operational `Builder.establish()` or packet forwarding is present.
- Until a validated forwarding core is integrated, the VPN service is **not registered in AndroidManifest.xml**; the app does not request `VpnService.prepare()` and cannot take system VPN ownership or be selected as Always-on VPN on any supported Android API 26+.
- The user interface explicitly reports that the provider core is not linked. CI checks the unregistered VPN service, consent-free UI, lack of active VPN service and unchanged emulator network interfaces.
- Historical debug build-pack `delivery/FreeNetHub_4.2.0_Android_BuildPack_Debug.apk` is **not an accepted functional VPN installer** and must not be treated as a V445 device-acceptance artifact. Historic debug signatures are not production signing.
- Build/static/emulator Fail-Closed verification is distinct from actual mobile VPN operation. Real forwarding core, licensing, production signing, install/update and physical connection tests remain **OPEN / UNPROVEN**.
