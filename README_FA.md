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

## Linux R9 / R37

نسخهٔ فعلی Linux برابر `4.2.0-linux.9-r37` است و معماری UI ویندوز R37 را با پنج بخش Dashboard / Methods / Nodes / Tools / Settings روی GTK4/Libadwaita پیاده می‌کند.

- Browser: AUTO، Node Pool، WARP، GOOL، CFON، Tor/obfs4/Snowflake، Custom و Direct.
- Node Pool: import URL/File/Clipboard، public refresh، Test All مستقل، benchmark محدود، sort/filter، Favorite/Pin، metadata، History و Export Raw/Base64.
- sing-box 1.14.2 و warp-plus 1.2.6 به‌صورت app-local و hash-pinned از release رسمی upstream provision می‌شوند.
- Full-System در Linux R9 فقط WARP رسمی است؛ Full-System Node بدون helper privileged و acceptance مستقل ادعا نمی‌شود.
- Console Gateway software policy و rollback حفظ شده‌اند؛ تست فیزیکی game/country همچنان external gate است.
- UpdateCheck revision-aware است و downgrade را نصب نمی‌کند؛ Install Update فقط asset جدیدتر با SHA-256 معتبر را می‌پذیرد.
- نصب و بازشدن برنامه هیچ VPN/proxy/Hotspot را خودکار روشن نمی‌کند و route موجود—including VPN خارجی—در acceptance دقیق package بدون تغییر باقی ماند.

بستهٔ پذیرفته‌شده: `FreeNetHub_4.2.0_Linux_R9.zip`.
## به‌روزرسانی Android/iOS روی main

Android 4.2.0 علاوه بر clean build، در hosted emulator چرخه permission واقعی VpnService را به‌صورت fail-closed PASS کرده است؛ forwarding core و signing تولیدی هنوز gate خارجی‌اند. iOS نیز static و hosted simulator build/install/launch/relaunch را PASS کرده، اما forwarding core تولیدی، Apple signing/provisioning و runtime روی دستگاه فیزیکی همچنان gate خارجی هستند.

## iOS static gate

برای iOS، extension point و entitlement مربوط به Packet Tunnel تأیید شده‌اند و startTunnel تا قبل از اتصال forwarding core به‌صورت fail-closed رد می‌شود. build/signing/device runtime هنوز OPEN است.
