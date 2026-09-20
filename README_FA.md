# FreeNet Hub 4.1.2

وضعیت پذیرفته‌شده Windows فقط Browser/Proxy Scope است و Full-System VPN هنوز ادعای PASS ندارد.

در تست نهایی روی سیستم هدف، WARP / GOOL / CFON / TOR برای HTTPS واقعی PASS شدند و EXE مستقل، Start Menu، آیکون Taskbar، Minimize-to-Tray-to-Restore، single-instance و عدم بازشدن Terminal نیز PASS شدند. route/DNS/WinINET proxy قبل و بعد از تست تغییر نکرد.

Linux فعلاً source/static PASS است و runtime provider gate باز است. Android و iOS build/integration packهای native و fail-closed هستند و تا زمانی که forwarding core واقعی و تست runtime کامل نشود به‌عنوان VPN نهایی معرفی نمی‌شوند.

برای Windows ابتدا dependencyهای local را با Setup-WindowsDependencies.ps1 ثبت کنید و سپس Install-Windows.ps1 را اجرا کنید. فایل app/dependencies.json محلی است و وارد Git نمی‌شود.

## اصلاح 4.1.2
بررسی مسیر خاموش دیگر به proxy مرده درخواست نمی‌فرستد و زمان شکست را latency نشان نمی‌دهد. مسیر خاموش با پیام «مسیر متصل نیست» و مقادیر — نمایش داده می‌شود؛ همچنین بازشدن دوبارهٔ پنل، provider فعال متعلق به برنامه را با Inventory خواندنی تشخیص می‌دهد.
