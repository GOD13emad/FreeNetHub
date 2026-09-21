# FreeNet Hub 4.2.0 - iOS

- Framework: SwiftUI + `NEPacketTunnelProvider`.
- Metadata: app/extension روی version 4.2.0 و build 420 همگام شده‌اند.
- Static fail-closed gate: PASS.
- `NSExtensionPointIdentifier = com.apple.networkextension.packet-tunnel` و entitlement `packet-tunnel-provider` برای app/extension وجود دارند.
- `PacketTunnelProvider.startTunnel` تا وقتی forwarding core لینک نشده عمداً `coreNotLinked` برمی‌گرداند و هیچ `setTunnelNetworkSettings` فعال نمی‌کند.
- این وضعیت build/runtime VPN acceptance نیست. macOS/Xcode build، Apple signing/entitlement provisioning، forwarding core و device runtime هنوز OPEN هستند.
