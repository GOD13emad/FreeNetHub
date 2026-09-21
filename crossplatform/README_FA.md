# FreeNet Hub 4.2.0 - Cross-platform

- Windows: release 4.2.0 software-accepted for browser/proxy + WARP PC_TUNNEL + Console Gateway software path. Physical console/game field validation remains separate.
- Linux: source/static checks pass in WSL; UI launch and real WARP/Tor provider runtime remain platform-runtime gates until the required Linux packages/providers are present and exercised.
- Android: native VpnService integration/build pack remains fail-closed because the packet-forwarding core is not linked.
- iOS: native NEPacketTunnelProvider integration/build pack remains fail-closed until forwarding core, entitlements/signing and runtime validation are completed.

Static/build success is never promoted to runtime VPN acceptance.
