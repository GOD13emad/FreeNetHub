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

نسخهٔ native Linux 4.2.0-linux.8 روی Ubuntu 24.04.5 software-accepted است: UI بومی GTK4/Libadwaita، single-instance، دکمه‌های minimize/maximize/close، WARP safe-trial و rollback توکن‌محور، مالکیت Console Gateway بر اساس UUID، migration سخت‌گیرانهٔ profile قدیمی، Firefox profile جدا، integrity launcher و uninstaller محدود به منابع owned همگی تأیید شده‌اند.

در شبکهٔ پذیرش نهایی، Direct Tor در پنجرهٔ دستی ۹۰ ثانیه تا bootstrap 55% رسید؛ AUTO فقط ۳۰ ثانیه Direct را probe کرد و سپس به obfs4 رفت و در مجموع 38.91 ثانیه به bootstrap 100% و HTTPS egress رسید. Snowflake بدون bridge runtime معتبر fail-closed می‌ماند. bridgeهای واقعی در source عمومی ذخیره نمی‌شوند.

برای سازگاری کنسول، Hotspot به‌صورت صریح WPA2/RSN با PMF غیرفعال تنظیم می‌شود و برای profile owned، PSK در Prepareهای تکراری بدون درخواست کاربر تغییر نمی‌کند.

state خصوصی Linux نیز harden شده است: directoryهای app/evidence/tor برابر 700 و state/guard files حساس برابر 600 هستند و upgrade فایل‌های قدیمی را migrate می‌کند.

گیت باز Linux فقط اعتبارسنجی DHCP/UDP/game/country با کنسول فیزیکی است؛ software gateway خودش پذیرفته شده است.

Firefox Snap در R7 از profile مجاز Snap استفاده می‌کند و installer UI قدیمی را پس از update reload می‌کند.

## به‌روزرسانی Android/iOS روی main

Android 4.2.0 با JDK 17، Gradle 8.9، SDK/Build Tools 35 clean-build شده و APK debug با versionCode=420 و امضای v2 معتبر دارد. با این حال forwarding core هنوز لینک نشده و runtime VPN ادعا نمی‌شود. iOS نیز از نظر metadata به 4.2.0 همگام شده ولی build/signing/device runtime هنوز gate خارجی است.

## iOS static gate

برای iOS، extension point و entitlement مربوط به Packet Tunnel تأیید شده‌اند و startTunnel تا قبل از اتصال forwarding core به‌صورت fail-closed رد می‌شود. build/signing/device runtime هنوز OPEN است.
