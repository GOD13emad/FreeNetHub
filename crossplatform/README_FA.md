# FreeNet Hub 4.2.0 - Cross-platform

- Windows: release 4.2.0 software-accepted for Browser/Proxy + WARP PC_TUNNEL + Console Gateway software path. Physical console/game field validation remains separate.
- Linux/WSL: source/static, installer/UI smoke, and Tor runtime are accepted on Ubuntu 24.04.4 WSL. Direct Tor, Snowflake and obfs4 each reached bootstrap 100%, passed HTTPS through the local SOCKS path, and stopped cleanly. Private bridge files are runtime-only and excluded from source/public release material.
- Linux WARP: remains a separate native-Linux runtime gate. In the current WSL acceptance environment `warp-cli` is absent and the app fails closed without network mutation.
- Android: native VpnService integration/build pack remains fail-closed because the packet-forwarding core is not linked.
- iOS: native NEPacketTunnelProvider integration/build pack remains fail-closed until forwarding core, entitlements/signing and runtime validation are completed.

Static/build success is never promoted to runtime VPN acceptance, and WSL results are not represented as native-Linux WARP acceptance.
