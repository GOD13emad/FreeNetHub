# FreeNet Hub 4.2.0

نسخه Windows 4.2.0 برای Browser/Proxy، تونل کامل PC با WARP، و مسیر نرم‌افزاری Console Gateway پذیرش شده است.

- PC_TUNNEL از clean install واقعی: warp=on، YouTube=204، UDP/STUN=PASS و rollback=PASS.
- Installer: clean install/bootstrap/uninstall=PASS.
- Console Gateway: شبیه‌سازی Linux-router و attach/detach آداپتور Realtek با WSL=PASS.
- تست بازی از کنسول فیزیکی هنوز OPEN است چون لینک اختصاصی هنگام پذیرش نهایی قطع بود.
- installer امضای Authenticode ندارد؛ SHA-256 منتشرشده را بررسی کنید.
- providerهای مرورگری داخل repository/installer بازتوزیع نمی‌شوند؛ Gateway core و sing-box پین‌شده provision می‌شوند.

برای Windows از asset نهایی FreeNetHub_4.2.0_FINAL_Setup.exe در Release v4.2.0 استفاده کنید.

## به‌روزرسانی Linux روی main

Tag و assetهای v4.2.0 تغییر نکرده‌اند. نسخهٔ native Linux `4.2.0-linux.4` روی Ubuntu 24.04.5 software-accepted است: UI بومی GTK4/Libadwaita، single-instance، دکمه‌های minimize/maximize/close، WARP safe-trial و rollback توکن‌محور، ownership safety، Tor Direct/obfs4، Firefox profile جدا، integrity launcher و Console Gateway software path همگی runtime PASS دارند.

Snowflake حفظ شده و بدون bridge runtime معتبر fail-closed می‌شود؛ bridgeهای واقعی obfs4/Snowflake در source عمومی نگهداری نمی‌شوند. WSL evidence قبلی Direct/Snowflake/obfs4 نیز حفظ شده است. گیت باز Linux فقط اعتبارسنجی DHCP/UDP/game/country با کنسول فیزیکی است؛ software gateway خودش پذیرفته شده است.

## به‌روزرسانی Android/iOS روی main

Android 4.2.0 با JDK 17، Gradle 8.9، SDK/Build Tools 35 clean-build شده و APK debug با versionCode=420 و امضای v2 معتبر دارد. با این حال forwarding core هنوز لینک نشده و runtime VPN ادعا نمی‌شود. iOS نیز از نظر metadata به 4.2.0 همگام شده ولی build/signing/device runtime هنوز gate خارجی است.

## iOS static gate

برای iOS، extension point و entitlement مربوط به Packet Tunnel تأیید شده‌اند و startTunnel تا قبل از اتصال forwarding core به‌صورت fail-closed رد می‌شود. build/signing/device runtime هنوز OPEN است.
