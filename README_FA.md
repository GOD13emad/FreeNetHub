# FreeNet Hub 4.3.8 — نسخه عمومی ویندوز R52 و لینوکس R20

**مرجع رسمی نصب:** https://github.com/GOD13emad/FreeNetHub/releases/tag/v4.3.8-r52-windows-stable

## Windows R52 — نسخه عمومی

- نام فایل: `FreeNetHub_4.3.8_R52_Setup.exe`
- SHA-256: `A48F689B22940C9D752FADB6372B849948B18192F3A30D4FC3971C15827F9883`
- نسخه: `4.3.8-r52-stale-node-health-ttl`
- ارتقا از R51 در همان مسیر نصب و با شناسه ثابت انجام می‌شود، اما وجود اتصال فعال یا Listener متعلق به برنامه باعث توقف ایمن ارتقا می‌شود.
- CI رسمی شماره [363](https://github.com/GOD13emad/FreeNetHub/actions/runs/38477116892) روی commit دقیق `0a89fbbab80e603191040471531d6ef1e287df26` با موفقیت کامل پایان یافته است.
- این نصب‌کننده **به انتخاب ناشر بدون امضای دیجیتال** منتشر شده است. ممکن است Windows SmartScreen یا Smart App Control آن را مسدود کند. برای نصب، محافظت امنیتی سیستم را غیرفعال نکنید.

## Linux R20 — نسخه عمومی

- نام فایل: `FreeNetHub_4.2.0_Linux_R20.zip`
- SHA-256: `5973D721EC2D93F7D500187EBC9BB4A5CA06AD73A937BC9AAD936E7C1D745D3B`
- نسخه نصب‌شده تأییدشده: `4.2.0-linux.20-r47`
- ممیزی زنده ۱۴ اکتبر ۲۰۲۶: انطباق ۹/۹ هش نصب و پاسخ HTTPS برابر 200 از مسیر CFON همراه با حفظ مسیر پیش‌فرض و Tailscale.
- **CFON در این شواهد صرفاً در محدوده مرورگر/پراکسی محلی تأیید شده است**؛ پوشش کامل سیستم و نبود نشت DNS در لینوکس هنوز اثبات نشده است.

## Windows R51 — نسخه قبلی

- R51 صرفاً مرجع نسخه قبلی یا بازگشت کنترل‌شده است و جدیدترین نصب‌کننده عمومی نیست.
- در زمان فعالیت تونل یا Listener، ارتقای R52 نباید اجباری اجرا شود.

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

انتشار عمومی Windows R52 و Linux R20 فقط در محدوده آزمون‌های مستند تأیید شده است. جلوگیری از نشت DNS در تونل سراسری لینوکس، سازگاری نصب‌کننده بدون امضای R52 با Smart App Control، پذیرش GUI نصب واقعی روی دستگاه کاربر، Console فیزیکی، Forwarding موبایل و ورود تعاملی مرورگر پس از چالش Cloudflare هنوز گیت‌های باز هستند. پاسخ 403 ابزار خط فرمان با هدر cf-mitigated: challenge نه اثبات ورود موفق است و نه اثبات خرابی پراکسی.

هیچ برنامه‌ای در صورت قطع همهٔ مسیرهای بالادستی نمی‌تواند دسترسی اینترنت را تضمین کند.

## مرجع سورس و انتشار

برای نصب، نام فایل و SHA-256 دقیق دارایی‌های انتشار رسمی v4.3.8-r52-windows-stable معیار است؛ تغییرات احتمالی بعدی در مستندات شاخه `main` بدون بازسازی بسته نصب انجام می‌شوند. مخزن در حال حاضر **مجوز سراسری نرم‌افزاری ندارد** (مطابق `THIRD_PARTY_NOTICES.md`) و مجوز وابستگی‌ها برای سورس خود FreeNet Hub مجوز محسوب نمی‌شود. تعیین نوع مجوز به مالک پروژه مربوط است.

شواهد و محدودیت‌ها: SECURITY.md، Issues #30/#32 و evidence/.
