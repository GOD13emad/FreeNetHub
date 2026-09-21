# FreeNet Hub 4.2 Linux

- بازشدن UI هیچ اتصال یا تغییر شبکه‌ای ایجاد نمی‌کند.
- نصب پیشنهادی از source: `bash ./install.sh`؛ executable bit فایل zip لازم نیست.
- Tor روی SOCKS محلی `127.0.0.1:9909` مدیریت می‌شود و Start فقط وقتی PASS است که bootstrap به 100٪ برسد و HTTPS واقعی از همان SOCKS موفق شود.
- ترتیب fallback در صورت داشتن bridge خصوصی: Snowflake → Direct → obfs4. اگر bridge خصوصی Snowflake وجود نداشته باشد: Direct → obfs4.
- bridgeهای واقعی در source/Git نگهداری نمی‌شوند. فایل‌های خصوصی:
  - `~/.local/share/FreeNetHub/bridges_snowflake.txt`
  - `~/.local/share/FreeNetHub/bridges_obfs4.txt`
- نصب مجدد bridgeهای خصوصی موجود را overwrite نمی‌کند.
- WARP فقط با اقدام صریح کاربر و `warp-cli` رسمی وصل می‌شود. اتصال WARP با anti-lockout guard محدود شروع می‌شود و اگر Keep تأیید نشود auto-disconnect می‌شود.
- فرمان recovery محلی: `freenethub-recover`.
- WSL acceptance: UI dependency و Tor Direct/Snowflake/obfs4 start→HTTPS→stop PASS.
- Native Linux acceptance روی Ubuntu 24.04.5: WARP baseline `off`، connect `on`، YouTube 204، disconnect PASS و route/DNS/status به baseline برگشته‌اند.
- evidence عمومی: `evidence/LINUX_NATIVE_420_WARP_PUBLIC_ACCEPTANCE.json`.
