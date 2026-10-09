# FreeNet Hub 4.2.0 — Linux 4.2.0-linux.20-r47

نسخهٔ Linux R20 رابط و معماری محصولی R37 را با GTK4/Libadwaita ارائه می‌کند. بازشدن برنامه هیچ VPN، proxy یا Hotspot را خودکار روشن نمی‌کند.

R20 مسیر Browser برای NODE را به SOCKS محلی همان sing-box (`127.0.0.1:19460`) متصل می‌کند، DNS مرورگر را از همان SOCKS می‌فرستد و اجرای واقعی Firefox را با PID بررسی می‌کند؛ دکمه مرورگر عادی از مرورگر تونلی جداست.

## رابط R37

پنج بخش اصلی:
- Dashboard: وضعیت، Scope، روش، Ping و Benchmark.
- Methods: AUTO / NODE / WARP / TOR / CUSTOM / DIRECT / GOOL / CFON.
- Nodes: import URL/File/Clipboard، دریافت نود عمومی، Test All، Benchmark محدود، sort/filter، Favorite/Pin، metadata، History و Export Raw/Base64.
- Tools: Update، Node refresh، Inventory/Doctor، Direct speed، Console Gateway و Tor/Bridges.
- Settings: Theme، IP visibility، test path، timeoutها، country، home، custom proxy و monitor.

## Scopeها و backend واقعی

- Browser:
  - Node Pool با sing-box app-local و hash-pinned.
  - WARP / GOOL / CFON با warp-plus app-local و hash-pinned.
  - Tor Direct / obfs4 / Snowflake.
  - Custom HTTP/SOCKS proxy و Direct.
- Full System:
  - WARP رسمی Cloudflare، با ownership/rollback موجود.
  - Full-System Node در Linux R18 ادعا نمی‌شود؛ بدون helper privileged/CAP_NET_ADMIN fail-closed می‌ماند.
- Console:
  - NetworkManager-owned hotspot/gateway مستقل؛ physical game/country E2E همچنان gate خارجی است.

## Node Pool

Parser/config generator همان contract نود مشترک را reuse می‌کند و SS/VMess/VLESS/Trojan/Hysteria v1/Hysteria2/TUIC/AnyTLS را از share-link و ShadowTLS/SSH/Snell/SOCKS/HTTP CONNECT/Naive را از sing-box JSON امن می‌شناسد.

«دریافت نودهای جدید» فقط fetch/parse/merge می‌کند. Test All جداست و endpoint reachability را می‌سنجد. HTTPS proxy-health و throughput جداگانه سنجیده می‌شوند؛ endpoint باز هرگز به معنی proxy سالم اعلام نمی‌شود.

## Dependency integrity

Installer دو dependency را app-local provision می‌کند:
- sing-box 1.14.2 از release رسمی SagerNet با archive SHA-256 پین‌شده.
- warp-plus 1.2.6 از release رسمی bepass-org با archive SHA-256 پین‌شده.

Launcher قبل از اجرا `INSTALL.sha256` را روی source runtime و هر دو binary بررسی می‌کند.

## Update

UpdateCheck فقط assetهای Linux با الگوی `_Linux_RN.zip` را مقایسه می‌کند. revision پایین‌تر downgrade محسوب نمی‌شود. Install Update فقط asset جدیدتر HTTPS/GitHub را پس از SHA-256 معتبر دانلود و استخراج می‌کند و installer فقط UI FreeNet Hub را restart می‌کند؛ نصب، اتصال شبکه‌ای را خودکار روشن نمی‌کند.

## نصب

```bash
bash crossplatform/linux/install.sh
```

اگر Cloudflare WARP رسمی برای Full-System نصب نیست:

```bash
bash crossplatform/linux/install_warp_official.sh
```

## حریم خصوصی و rollback

State خصوصی در `~/.local/share/FreeNetHub` نگه‌داری می‌شود. runtime/evidence/tor mode 700 و state JSON/logها mode 600 دارند. Installer قبل از upgrade فایل‌های قبلی را backup می‌کند و route را تغییر نمی‌دهد.

## Gateهای خارجی

- Physical console DHCP/UDP/game/country E2E.
- Full-System Node privileged helper در Linux، تا زمانی که مستقل و fail-safe پذیرفته شود.


## R20 — تشخیص مقصد و انتخاب هوشمند CFON
- حالت AUTO مرورگر: Node، سپس CFON در صورت موفقیت تست Google به‌علاوه GitHub یا NVIDIA، سپس WARP و Tor. صرف Cloudflare Trace قبولی سایت‌ها محسوب نمی‌شود.
- دکمه «تست دسترسی سایت‌ها از داخل اتصال فعلی» چهار مقصد ثابت Google / GitHub / NVIDIA / ChatGPT را با SOCKS5H و DNS داخل پروکسی مالک‌دار آزمایش می‌کند؛ HTTP 403 یا challenge با PASS اشتباه نمی‌شود.
- تست در صورت نبود پروکسی مالک‌دار یا قطع‌شدن آن Fail-closed است. AUTO فقط Scope مرورگر را تغییر می‌دهد، TUN سیستم را خودکار تغییر نمی‌دهد.
- آزمایش مسیر OpenVPN عمومی و VPN Gate در اسناد پروژه پژوهشی است؛ این نسخه هیچ VPN داوطلبانه، ثبت‌کنندهٔ لاگ یا مسیر سراسری جدیدی را خودکار نصب/فعال نمی‌کند. CFON مرورگر با TCP قابل استفاده است، اما تونل کامل TCP/UDP به گیت مستقل نیاز دارد.
