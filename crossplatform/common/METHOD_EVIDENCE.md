# Cross-platform method and evidence

Primary references:
- Cloudflare WARP client: https://developers.cloudflare.com/warp-client/get-started/
- Cloudflare WARP Linux: https://developers.cloudflare.com/warp-client/get-started/linux/
- Android VpnService: https://developer.android.com/reference/android/net/VpnService
- Apple NEPacketTunnelProvider: https://developer.apple.com/documentation/networkextension/nepackettunnelprovider
- Hiddify multi-platform reference: https://github.com/hiddify/hiddify-app

Architecture:
- Linux uses explicit official warp-cli actions for system-wide WARP plus a separately owned local Tor SOCKS provider. Opening the UI never changes networking.
- Android provides a native VpnService integration shell, but does not call Builder.establish() until a real packet-forwarding core is linked.
- iOS provides a NEPacketTunnelProvider extension, but startTunnel fails closed with coreNotLinked until a real forwarding core, entitlement and signing are present.
- Static/build success is not runtime VPN acceptance.
