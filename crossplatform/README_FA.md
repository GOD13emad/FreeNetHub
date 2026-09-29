# FreeNet Hub 4.2.0 - Cross-platform

- Windows R37: public final release برای Browser / Full System / Console، Node Pool، update-root policy و installer lifecycle پذیرفته شده است.
- Linux R9 / 4.2.0-linux.9-r37: UI پنج‌بخشی R37، Node Pool واقعی با sing-box، WARP/GOOL/CFON مرورگری با warp-plus، Tor/bridges، Custom/Direct، Update، diagnostics و Console software path روی Ubuntu پذیرفته شده‌اند. Full-System WARP رسمی است؛ Full-System Node بدون helper privileged ادعا نمی‌شود.
- Linux installer هیچ اتصال شبکه‌ای را خودکار روشن نمی‌کند و dependencyهای sing-box/warp-plus را app-local و hash-pinned provision می‌کند.
- Android: hosted build/emulator fail-closed lifecycle PASS است؛ forwarding core و production signing هنوز OPEN.
- iOS: hosted static/simulator lifecycle PASS است؛ production packet-forwarding core، Apple signing/provisioning و physical-device runtime هنوز OPEN.
- Physical Console game/country E2E همچنان external hardware gate است.

Static/build success هرگز به runtime acceptance ارتقا داده نمی‌شود. Evidence platform-specific در پوشه `evidence/` ثبت می‌شود.
