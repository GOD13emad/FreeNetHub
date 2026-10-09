# FreeNet Hub 4.3.7 — نسخه عمومی جاری

مرجع نصب عمومی دقیقاً این Release است: https://github.com/GOD13emad/FreeNetHub/releases/tag/v4.3.7-r20-linux-cfon-smart

## Windows R51 — نسخه عمومی

- نام فایل: `FreeNetHub_4.3.7_R51_Setup.exe`
- SHA-256: `8283803146E1625A31F0223487A63C05D7B7D9C3D8B59D1A7432D14AB9D4FF11`
- Revision نصب: `4.3.7-r51-protocol-expansion-2`
- ممیزی زنده در 2026-10-09: تطابق ۱۷/۱۷ هش نصب، CFON مرورگر با GitHub HTTP 200 و Tailscale فعال.
- امضای Authenticode ناشر با اعتماد عمومی برای این نصب‌کننده ثابت نشده است.

## Linux R20 — نسخه عمومی

- نام فایل: `FreeNetHub_4.2.0_Linux_R20.zip`
- SHA-256: `5973D721EC2D93F7D500187EBC9BB4A5CA06AD73A937BC9AAD936E7C1D745D3B`
- Revision نصب: `4.2.0-linux.20-r47`
- ممیزی زنده در 2026-10-09: تطابق ۹/۹ هش نصب، CFON اتریش GitHub HTTP 200 و Google HTTP 204 با حفظ Tailscale.
- **CFON در Linux فقط Browser است**؛ موفقیت تونل خصوصی UID ایزوله، حفاظت همهٔ سیستم و رفع نشت DNS میزبان را ثابت نمی‌کند.

## Windows R52 — منتشرنشده

PR #34 در https://github.com/GOD13emad/FreeNetHub/pull/34 همچنان Draft است. CI روی SHA دقیق با ۱۰/۱۰ Job موفق، نصب تازه، ارتقای R51 به R52 و بازگشت کنترل‌شده R52 به R51 را روی Windows آزمایشی ثابت کرده است: https://github.com/GOD13emad/FreeNetHub/actions/runs/37972493989 . امضای معتبر عمومی و پذیرش GUI روی دستگاه فعال هنوز بازند؛ R52 مرجع نصب عمومی نیست.

## امکانات فعلی

- UI پنج‌بخشی Dashboard / Methods / Nodes / Tools / Settings
- مرزبندی صریح Browser / Full System / Console
- AUTO، Node Pool، WARP، GOOL، CFON، Tor/obfs4/Snowflake، Custom و Direct در مسیرهایی که runtime و platform آن‌ها اعتبارسنجی شده است
- import نودهای SS، VMess، VLESS، Trojan، Hysteria v1/v2، TUIC و AnyTLS
- import کنترل‌شدهٔ sing-box JSON برای ShadowTLS، SSH، Snell، SOCKS، HTTP CONNECT و Naive
- fail-closed برای ورودی‌های ناامن یا unsupported
- Refresh، Test، benchmark، رتبه‌بندی، Favorite/Pin، metadata، sort/filter و export نودها
- Online Update revision-aware با جلوگیری از downgrade
- اجرای عادی برنامه هیچ VPN/proxy/network path را خودکار روشن نمی‌کند

## مرز اعتبارسنجی

محصول عمومی Windows R51 و Linux R20 فقط برای محدوده‌های واقعاً آزموده‌شده پذیرفته شده است. گیت‌های جداگانهٔ رفع نشت DNS تمام‌سیستم Linux، امضای معتبر عمومی Windows R52، پذیرش GUI روی سیستم فعال، آزمون فیزیکی Console، Forwarding و امضای تولیدی موبایل و ورود تعاملی مرورگر پس از چالش Cloudflare بازند. HTTP 403 به‌معنای ورود موفق نیست.

هیچ برنامه‌ای در صورت قطع همهٔ مسیرهای بالادستی نمی‌تواند دسترسی اینترنت را تضمین کند.

## مرجع سورس و انتشار

برای نصب، نام فایل و SHA-256 واقعی Assetهای Release v4.3.7-r20-linux-cfon-smart معیار است؛ شاخهٔ `main` می‌تواند سورس جدیدتر داشته باشد. مخزن در حال حاضر **مجوز سراسری نرم‌افزاری ندارد** (مطابق `THIRD_PARTY_NOTICES.md`) و مجوز وابستگی‌ها برای سورس خود FreeNet Hub مجوز محسوب نمی‌شود. تعیین نوع مجوز به مالک پروژه مربوط است.

شواهد و محدودیت‌ها: SECURITY.md، Issues #30/#32 و evidence/.
