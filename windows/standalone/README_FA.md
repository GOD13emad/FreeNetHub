# FreeNet Hub 4.1.2 — Windows Standalone Shell

این بسته نسخهٔ اصلاح‌شده و runtime-tested پوستهٔ مستقل Windows است.

- اجرای کاربر از `FreeNetHub.exe` انجام می‌شود؛ PowerShell فقط backend مخفی است و Windows Terminal/OpenConsole باز نمی‌شود.
- Start Menu مستقیماً به EXE اشاره می‌کند و آیکون EXE برای Start/Taskbar/Tray استفاده می‌شود.
- Minimize پنجره را به System Tray می‌برد و اجرای دوباره همان instance را Restore می‌کند.
- AppUserModelID در process رابط روی `FreeNetHub.Desktop` تنظیم می‌شود.
- installer قبل از تغییر EXE/Shortcut backup می‌سازد و route/DNS/proxy/Firefox/Startup را تغییر نمی‌دهد.
- installer ابتدا `MANIFEST.json` را verify می‌کند و از EXE پذیرفته‌شدهٔ داخل بسته استفاده می‌کند؛ compiler فقط fallback است.

## نصب

```powershell
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File .\Install-FreeNetHubShell.ps1 -Root "C:\Users\<USER>\source\repos\FreeNetHub"
```

## وضعیت پذیرش روی سیستم هدف

Runtime acceptance برای shell Windows PASS شده است: EXE 4.1.2.0، single-instance، Minimize→Tray، Restore، icon handle، AppUserModelID و نبود Terminal. جزئیات sanitized در `RUNTIME_ACCEPTANCE.json` است.

این پذیرش فقط برای Windows browser/proxy scope است و به معنی PASS شدن Full-System TUN، DNS/IPv6 leak، kill switch یا UDP/game نیست.
