# FreeNet Hub 4.2 — Windows Standalone Shell

این بسته پوستهٔ مستقل Windows برای FreeNet Hub 4.2 است.

- اجرای کاربر از `FreeNetHub.exe` انجام می‌شود؛ PowerShell backend مخفی است و Windows Terminal/OpenConsole باز نمی‌شود.
- Start Menu مستقیماً به EXE اشاره می‌کند و آیکون EXE برای Start/Taskbar/Tray استفاده می‌شود.
- Minimize پنجره را به System Tray می‌برد و اجرای دوباره همان instance را Restore می‌کند.
- AppUserModelID روی `FreeNetHub.Desktop` تنظیم می‌شود.
- خود shell با `asInvoker` اجرا می‌شود؛ Administrator دائمی نیست.
- بازشدن برنامه route/DNS/proxy/TUN/firewall را تغییر نمی‌دهد.
- عملیات Full-PC Tunnel و Console Gateway فقط از تب «گیت‌وی» و با UAC جداگانه انجام می‌شوند.
- installer قبل از جایگزینی EXE/Shortcut backup می‌سازد و Startup خودکار نصب نمی‌کند.
- installer ابتدا `MANIFEST.json` را verify می‌کند و سپس EXE پذیرفته‌شدهٔ داخل بسته را نصب می‌کند.

## نصب

```powershell
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File .\Install-FreeNetHubShell.ps1 -Root "C:\Users\<USER>\source\repos\FreeNetHub"
```

## پذیرش runtime

Shell 4.2.0.0 روی سیستم هدف PASS شده است: single-instance، Minimize→Tray، Restore، icon، AppUserModelID، نبود Terminal/OpenConsole و نبود mutation شبکه هنگام launch.

جزئیات sanitized در `RUNTIME_ACCEPTANCE.json` است.
