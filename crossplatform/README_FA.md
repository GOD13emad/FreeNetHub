# FreeNet Hub 4.2.0 - Cross-platform

- Windows: release 4.2.0 software-accepted for Browser/Proxy + WARP PC_TUNNEL + Console Gateway software path. Physical console/game field validation remains separate.
- Linux native: 4.2.0-linux.6 روی Ubuntu 24.04.5 پذیرفته شده است. WARP، GTK4/Libadwaita UI، UUID-owned Console Gateway، strict legacy migration، isolated Firefox، integrity/install/uninstall lifecycle و AUTO Tor fallback runtime evidence دارند؛ AUTO در پذیرش نهایی پس از Direct probe به obfs4 رفت و bootstrap=100/HTTPS=PASS شد. Console Gateway در R6، WPA2/RSN+PMF-disabled و PSK پایدار برای profile owned دارد.
- Linux Snowflake: provider و UI حفظ شده‌اند و bridge material واقعی runtime-only است. بدون bridge معتبر fail-closed می‌شود؛ public tree هیچ bridge فعال ندارد. WSL evidence تاریخی Direct/Snowflake/obfs4 همچنان موجود است.
- Android: clean debug build برای 4.2.0 PASS است؛ VpnService declaration/permission و fail-closed shell تأیید شده‌اند. packet-forwarding core و device runtime/production signing هنوز OPEN هستند.
- iOS: metadata 4.2.0 و static fail-closed gate PASS است؛ extension point/entitlement معتبرند و startTunnel بدون core عمداً رد می‌شود. macOS/Xcode build، signing، forwarding core و device runtime هنوز OPEN هستند.

Static/build success هرگز به runtime acceptance ارتقا داده نمی‌شود. Linux native acceptance در `evidence/LINUX_NATIVE_420_PUBLIC_ACCEPTANCE.json` به‌صورت sanitized ثبت شده است.
