# FreeNet Hub 4.2.0 - Cross-platform

- Windows: release 4.2.0 software-accepted for Browser/Proxy + WARP PC_TUNNEL + Console Gateway software path. Physical console/game field validation remains separate.
- Linux/WSL: source/static, installer/UI smoke, and Tor runtime are accepted on Ubuntu 24.04.4 WSL. Direct Tor، Snowflake و obfs4 هر سه bootstrap=100، HTTPS=PASS و Stop=PASS دارند. bridgeهای واقعی runtime-only و خارج از source/public release هستند.
- Linux WARP: gate جداگانهٔ native-Linux است. در محیط WSL فعلی `warp-cli` وجود ندارد و برنامه fail-closed می‌ماند.
- Android: clean debug build برای 4.2.0 **PASS** است؛ VpnService declaration/permission و fail-closed shell تأیید شده‌اند. packet-forwarding core و device runtime/production signing هنوز OPEN هستند.
- iOS: metadata 4.2.0 و static fail-closed gate PASS است؛ extension point/entitlement معتبرند و startTunnel بدون core عمداً رد می‌شود. macOS/Xcode build، signing، forwarding core و device runtime هنوز OPEN هستند.

Static/build success هرگز به runtime VPN acceptance ارتقا داده نمی‌شود.
