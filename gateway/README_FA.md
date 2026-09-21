# FreeNet Hub Gateway 4.2.0

این زیرسیستم دو حالت مجزا دارد:

1. **PC_TUNNEL** — ترافیک اینترنتی کامپیوتر وارد TUN مدیریتی FreeNet Hub می‌شود. LAN خصوصی و transport خود provider برای جلوگیری از loop مستقیم می‌مانند.
2. **CONSOLE_ONLY** — کامپیوتر روی اینترنت اصلی خود باقی می‌ماند و ترافیک کنسول از پورت شبکه اختصاصی به router داخل WSL2 و سپس provider تأییدشده هدایت می‌شود.

## وضعیت پذیرش 4.2.0

### PC_TUNNEL — PASS روی سیستم هدف
- اجرای واقعی از یک clean install انجام شده است.
- Cloudflare trace: `warp=on`.
- YouTube generate_204: `204`.
- UDP/STUN: PASS.
- Stop/rollback: PASS.
- پس از rollback، default route، DNS و WinINET با baseline یکسان بوده‌اند و TUN/listener متعلق به پروژه باقی نمانده است.
- شواهد: `evidence/PC_TUNNEL_CLEAN_INSTALL_420_ACCEPTANCE.json` و `evidence/PC_TUNNEL_CLEAN_INSTALL_420_STOP.json`.

### CONSOLE_ONLY — Software path PASS / physical field gate OPEN
- معماری WSL2 Linux router با TUN و nftables leak guard در simulation واقعی TCP/UDP به کشور DE PASS شده است.
- Realtek USB GbE با usbipd به WSL attach/detach شده و ownership به Windows برگشته است.
- در آخرین ممیزی کابل/کنسول واقعی متصل نبود و Realtek وضعیت `Disconnected / 0 bps` داشت؛ بنابراین DHCP/route/game واقعی از خود کنسول هنوز **OPEN / UNPROVEN** است.
- شواهد: `evidence/CONSOLE_WSL_LINUX_ROUTER_SIM_ACCEPTANCE.json` و `evidence/CONSOLE_USB_REALTEK_WSL_ACCEPTANCE.json`.

## سخت‌افزار سیستم هدف

- uplink اصلی: Intel I226-V / `Ethernet 3`
- پورت اختصاصی کنسول: Realtek USB GbE / `Ethernet`
- IP سمت router برای Console Mode: `192.168.77.1/24`
- تنظیم دستی پیشنهادی کنسول در صورت نیاز:
  - IP: `192.168.77.2`
  - Mask: `255.255.255.0`
  - Gateway: `192.168.77.1`
  - DNS: `1.1.1.1`

## Provider و portability

- sing-box 1.14.0 برای Gateway با SHA-256 ثابت provision می‌شود و داخل runtime نصب FreeNet Hub قرار می‌گیرد.
- PC_TUNNEL فعلی روی WARP browser provider آزموده شده است.
- providerهای مرورگری WARP/Tor/GOOL/CFON در installer بازتوزیع نمی‌شوند؛ اگر روی سیستم وجود نداشته باشند، Inventory آن‌ها را Missing گزارش می‌کند و activation نباید به‌صورت ضمنی DIRECT شود.
- برای Console country mode، WireGuard profile واردشده باید TCP، UDP و country را runtime تأیید کند. private key فقط در `gateway/runtime/` نگه داشته می‌شود و وارد Git/Brain نمی‌شود.
- provider محلی آزمایشگاهی DE که برای simulation استفاده شد جزو installer عمومی نیست و نباید به‌عنوان dependency قابل‌انتقال فرض شود.

## Safety / rollback

- UI اصلی دائماً Administrator نیست؛ mutation شبکه فقط در action صریح elevated انجام می‌شود.
- Gateway manifest قبل از action hash/size فایل‌های authoritative را بررسی می‌کند.
- PC_TUNNEL در failure مسیر apply را rollback می‌کند.
- Console Mode ownership آداپتور، WSL state و provider را محدود نگه می‌دارد؛ leak guard اجازه خروج مستقیم subnet کنسول از uplink را نمی‌دهد.
- uninstall به‌صورت fail-closed ابتدا وضعیت Gateway را قابل‌اثبات می‌کند؛ در صورت cleanup نامطمئن حذف برنامه متوقف می‌شود.
- هیچ reboot/shutdown/logoff خودکار وجود ندارد.

## Installer 4.2.0

Installer نهایی:
`delivery/FreeNetHub_4.2.0_FINAL_Setup.exe`

Acceptance:
- clean install: PASS
- runtime bootstrap: PASS
- Gateway core provisioning: PASS
- shell single-instance / tray / restore / taskbar icon / AppUserModelID / no-new-Terminal: PASS
- uninstall cleanup و uninstaller end-to-end: PASS
- Authenticode: امضای trusted موجود نیست؛ صحت build با SHA-256 release کنترل می‌شود.

Authority نهایی: `evidence/FINAL_420_ACCEPTANCE.json`.
