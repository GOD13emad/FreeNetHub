# FreeNet Hub 4.3.7

نسخهٔ نهایی دسکتاپ FreeNet Hub برای Windows و Linux روی Release عمومی **v4.3.7** قرار دارد.

## نصب نهایی Windows

فقط این فایل را برای نصب جدید استفاده کنید:

`FreeNetHub_4.3.7_R51_Setup.exe`

SHA-256:

`4CCAE665D9F641BEC3FACF2BFDB908F5E727BDC32F278A91EA2E6C3BFE8208A3`

Revision پذیرفته‌شده:

`4.3.7-r51-protocol-expansion-2`

اعتبارسنجی تازه روی سیستم مالک در 2026-10-06:
- regression کامل: **252/252 PASS**
- تطابق دقیق RELEASE نصب‌شده با source: PASS
- تطابق app manifest: PASS
- تطابق gateway manifest: PASS
- revision محلی و remote هر دو 51 و آپدیت معوق وجود ندارد

Installer ویندوز فعلاً Authenticode عمومی معتبر ندارد، چون signing identity خارجی trusted فراهم نشده است. این یک gate خارجی signing است و defect نرم‌افزار دسکتاپ محسوب نمی‌شود.

## نصب نهایی Linux

فقط این بسته را برای نصب جدید استفاده کنید:

`FreeNetHub_4.2.0_Linux_R18.zip`

SHA-256:

`3C9254840C85B6D7305B0986209FF96EBEE578193D193538E8E8D45924ECBCD7`

نسخهٔ نصب‌شدهٔ پذیرفته‌شده:

`4.2.0-linux.18-r45`

اعتبارسنجی تازه:
- integrity نصب‌شده: **9/9 PASS**
- selftest: PASS
- scope policy: PASS
- browser profile: PASS
- console policy: PASS
- private-state permissions: PASS
- parity با source مشترک Windows/Linux: PASS
- update-revision regression: PASS
- مسیر Browser برای NODE روی SOCKS5 `127.0.0.1:19460` با remote DNS: PASS
- اجرای Snap Firefox از داخل FreeNet Hub: PASS
- trace زندهٔ تونل: DE و YouTube HTTP 204: PASS
- تست مستقیم ZIP استخراج‌شده: PASS
- checkout لینوکس و ویندوز روی authority یکسان `main`

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

نسخهٔ دسکتاپ Windows و Linux بر اساس evidence فعلی نهایی است. موارد زیر gateهای مستقل خارجی هستند:
- Windows Authenticode با زنجیرهٔ public trust
- تست فیزیکی Console/Game/Country
- forwarding/signing/runtime تولیدی Android و iOS روی دستگاه واقعی

در صورت قطع همهٔ مسیرهای فیزیکی/upstream، هیچ نرم‌افزاری نمی‌تواند اتصال را تضمین کند.

## Authority

Authority عمومی source: شاخهٔ `main` در یا بعد از commit نهایی مالک:

`09b8483851ed900e16784f2ef0cd837ecee90c9b`

Evidence تاریخی برای audit در repository نگه داشته می‌شود، اما نسخه‌های قدیمی authority نصب نیستند. برای نصب جدید فقط **v4.3.7** را استفاده کنید.
