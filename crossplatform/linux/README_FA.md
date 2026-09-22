# FreeNet Hub 4.2.0 — Linux

نسخهٔ Linux با UI بومی GTK4/Libadwaita و اتصال صریح (explicit-connect).

## وضعیت پذیرفته‌شده

- WARP رسمی: اتصال `warp=on`، حفظ کانال کنترل، disconnect و بازگشت baseline تأیید شده است.
- WARP safe-trial: watchdog توکن‌محور، stale-guard و ownership safety تست شده‌اند.
- Tor Direct و obfs4: bootstrap 100% و HTTPS egress تأیید شده‌اند.
- Snowflake: provider و UI حفظ شده‌اند؛ بدون bridge runtime معتبر fail-closed می‌شود. bridge خصوصی در Git ذخیره نمی‌شود.
- Firefox اختصاصی: پروفایل جداگانه با SOCKS remote-DNS؛ پروفایل اصلی Firefox تغییر نمی‌کند.
- Console Gateway: Hotspot نرم‌افزاری روی آداپتور ثانویه با WARP، IPv4 forwarding و rollback تأیید شده است.
- Window UX: single-instance، icon، `Terminal=false` و دکمه‌های minimize/maximize/close تأیید شده‌اند.
- Integrity: launcher قبل از اجرا SHA-256 فایل‌های نصب‌شده را بررسی می‌کند.

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
