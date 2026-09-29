# FreeNet Hub 4.2.0

Windows R37 با رابط پنج‌بخشی Dashboard / Methods / Nodes / Tools / Settings و مرزبندی صریح Browser / Full System / Console پذیرش نهایی شده است.

- Full-System WARP از مسیر رسمی Gateway: PASS؛ دریافت آپدیت/نود هنگام TUN از مسیر pre-TUN پایه اثبات شده است.
- Direct base-speed و benchmark مرورگر WARP: PASS.
- Node refresh فقط fetch/parse/merge می‌کند و تست endpointها با Test All جداست.
- Installer دقیق R37: exit=0، bootstrap=PASS، parity برای 17 فایل app + 17 فایل gateway=PASS، smoke هر پنج تب=PASS و route بدون تغییر.
- Hosted CI #99 برای Windows، Linux، Android build/emulator fail-closed، iOS static/simulator، Console virtual E2E، virtual signing و aggregate acceptance همگی PASS است.
- تست فیزیکی console/game/country و Authenticode قابل‌اعتماد همچنان gate خارجی هستند.
- providerهای اختیاری در نبود runtime معتبر fail-closed می‌مانند و fallback پنهان به DIRECT ندارند.

برای Windows از `FreeNetHub_4.2.0_R37_Final_Setup.exe` در Release `v4.2.0-r37-final` استفاده کنید. SHA-256 پذیرفته‌شده: `35491B9BCAD06263C063DA7559D67B206F01028E613232F101D249D552BA0C64`.

## به‌روزرسانی Linux روی main

نسخهٔ native Linux 4.2.0-linux.8 روی Ubuntu 24.04.5 software-accepted است: UI بومی GTK4/Libadwaita، single-instance، دکمه‌های minimize/maximize/close، WARP safe-trial و rollback توکن‌محور، مالکیت Console Gateway بر اساس UUID، migration سخت‌گیرانهٔ profile قدیمی، Firefox profile جدا، integrity launcher و uninstaller محدود به منابع owned همگی تأیید شده‌اند.

در شبکهٔ پذیرش نهایی، Direct Tor در پنجرهٔ دستی ۹۰ ثانیه تا bootstrap 55% رسید؛ AUTO فقط ۳۰ ثانیه Direct را probe کرد و سپس به obfs4 رفت و در مجموع 38.91 ثانیه به bootstrap 100% و HTTPS egress رسید. Snowflake بدون bridge runtime معتبر fail-closed می‌ماند. bridgeهای واقعی در source عمومی ذخیره نمی‌شوند.

برای سازگاری کنسول، Hotspot به‌صورت صریح WPA2/RSN با PMF غیرفعال تنظیم می‌شود و برای profile owned، PSK در Prepareهای تکراری بدون درخواست کاربر تغییر نمی‌کند.

state خصوصی Linux نیز harden شده است: directoryهای app/evidence/tor برابر 700 و state/guard files حساس برابر 600 هستند و upgrade فایل‌های قدیمی را migrate می‌کند.

گیت باز Linux فقط اعتبارسنجی DHCP/UDP/game/country با کنسول فیزیکی است؛ software gateway خودش پذیرفته شده است.

Firefox Snap در R7 از profile مجاز Snap استفاده می‌کند و installer UI قدیمی را پس از update reload می‌کند.

## به‌روزرسانی Android/iOS روی main

Android 4.2.0 علاوه بر clean build، در hosted emulator چرخه permission واقعی VpnService را به‌صورت fail-closed PASS کرده است؛ forwarding core و signing تولیدی هنوز gate خارجی‌اند. iOS نیز static و hosted simulator build/install/launch/relaunch را PASS کرده، اما forwarding core تولیدی، Apple signing/provisioning و runtime روی دستگاه فیزیکی همچنان gate خارجی هستند.

## iOS static gate

برای iOS، extension point و entitlement مربوط به Packet Tunnel تأیید شده‌اند و startTunnel تا قبل از اتصال forwarding core به‌صورت fail-closed رد می‌شود. build/signing/device runtime هنوز OPEN است.
