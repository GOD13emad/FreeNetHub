# FreeNet Hub 4.2.0 — Linux 4.2.0-linux.7

نسخهٔ Linux با UI بومی GTK4/Libadwaita و اتصال صریح (explicit-connect).

## وضعیت پذیرفته‌شده

- WARP رسمی: اتصال `warp=on`، حفظ کانال کنترل، disconnect و بازگشت baseline تأیید شده است.
- WARP safe-trial: watchdog توکن‌محور، stale-guard و ownership safety تست شده‌اند.
- Tor Direct و obfs4 پشتیبانی می‌شوند؛ Direct دستی تا ۹۰ ثانیه فرصت bootstrap دارد و AUTO پس از ۳۰ ثانیه Direct ناموفق به transport مقاوم‌تر fallback می‌کند. obfs4 در acceptance نهایی bootstrap 100% و HTTPS egress داشته است.
- Snowflake: provider و UI حفظ شده‌اند؛ بدون bridge runtime معتبر fail-closed می‌شود. bridge خصوصی در Git ذخیره نمی‌شود.
- Firefox اختصاصی: پروفایل جداگانه با SOCKS remote-DNS؛ پروفایل اصلی Firefox تغییر نمی‌کند.
- Console Gateway: Hotspot نرم‌افزاری روی آداپتور ثانویه با WARP، IPv4 forwarding و rollback تأیید شده است.
- سازگاری Wi-Fi کنسول: profile Hotspot به‌صورت صریح WPA2/RSN با PMF غیرفعال ساخته/به‌روزرسانی می‌شود؛ cipherها برای سازگاری بیشتر به انتخاب NetworkManager سپرده می‌شوند.
- پایداری credential: در profile owned، Prepare مجدد PSK معتبر قبلی را حفظ می‌کند و Start نیز policy امنیتی فعلی را قبل از activation enforce می‌کند.
- مالکیت پروفایل Console Gateway با UUID پایدار NetworkManager کنترل می‌شود؛ profile هم‌نامِ بدون ownership هرگز حذف یا فعال نمی‌شود. ارتقا از profile قدیمی فقط وقتی migrate می‌شود که یک profile واحد با device/SSID/AP/WPA-PSK/PSK/IPv4/IPv6 ثبت‌شده دقیقاً تطبیق داشته باشد.
- Window UX: single-instance، icon، `Terminal=false` و دکمه‌های minimize/maximize/close تأیید شده‌اند.
- Integrity: launcher قبل از اجرا SHA-256 فایل‌های نصب‌شده را بررسی می‌کند.
- حریم خصوصی state: directoryهای runtime/evidence/tor با mode 700 و state JSON/guard logs با mode 600 نگه‌داری می‌شوند؛ installer روی upgrade فایل‌های قدیمی را نیز بدون حذف به permissionهای خصوصی migrate می‌کند.

گیت باز: اعتبارسنجی فیزیکی DHCP/UDP/game/country با یک کنسول واقعی هنوز جداگانه لازم است؛ این مانع پذیرش software gateway نیست.

## نصب

روی Ubuntu 24.04:

```bash
bash crossplatform/linux/install.sh
```

اگر Cloudflare WARP نصب نیست، اسکریپت جداگانهٔ رسمی نیازمند احراز هویت مدیر است:

```bash
bash crossplatform/linux/install_warp_official.sh
```

باز شدن FreeNet Hub هیچ VPN، proxy یا Hotspot را خودکار روشن نمی‌کند.

## bridgeها

فایل‌های داخل repository فقط template هستند. material واقعی obfs4/Snowflake باید در runtime وارد شود و در تاریخچهٔ Git قرار نمی‌گیرد.

مسیر runtime:
- `~/.local/share/FreeNetHub/bridges_obfs4.txt`
- `~/.local/share/FreeNetHub/bridges_snowflake.txt`

## بازیابی

```bash
~/.local/bin/freenethub-recover
```

این فرمان WARP را disconnect می‌کند و در صورت وجود، سرویس Remote Commander کاربر را restart می‌کند.


## حذف برنامه

برای حذف فایل‌های برنامه بدون حذف bridge/evidence خصوصی:

```bash
freenethub-uninstall
```

uninstaller فقط profile کنسول را در صورتی حذف می‌کند که UUID ثبت‌شدهٔ همان profile با ownership پروژه تطبیق داشته باشد. Cloudflare WARP به‌عنوان package سیستمی خارجی حذف نمی‌شود. اسکریپت نصب WARP codename سیستم را از `/etc/os-release` می‌خواند و از repository رسمی Cloudflare استفاده می‌کند.

## Browser hotfix R7

- Firefox Snap دیگر profile تونلی را زیر `~/.local/share` نمی‌گیرد؛ برای عبور از confinement رسمی Snap از `~/snap/firefox/common/FreeNetHub/firefox-tunneled` استفاده می‌شود.
- profile فقط متعلق به FreeNet Hub است و `network.proxy.socks_remote_dns=true` برای Tor حفظ می‌شود.
- هنگام تعویض route فقط Firefox دقیق همین profile restart می‌شود؛ Firefox شخصی کاربر لمس نمی‌شود.
- installer اگر UI قدیمی FreeNet Hub باز باشد، فقط همان process دقیق را قبل از update می‌بندد و پس از نصب دوباره launcher واقعی desktop را اجرا می‌کند تا کد stale در حافظه نماند.
