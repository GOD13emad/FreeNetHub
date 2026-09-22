#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import threading

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk

APPDIR = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("freenethub_core", APPDIR / "freenet_hub_linux.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

ACCENT = "#39cdb4"

DARK_CSS = r"""
window { background: #0b1423; color: #ecf2fa; }
.sidebar { background: #132135; border-radius: 18px; padding: 18px; }
.card { background: #132135; border: 1px solid #2d435c; border-radius: 16px; padding: 18px; }
.soft { background: #1c3046; border-radius: 12px; padding: 12px; }
.title-big { font-size: 28px; font-weight: 700; color: #ecf2fa; }
.brand { font-size: 30px; font-weight: 800; color: #39cdb4; }
.muted { color: #a4b8cf; }
.metric { font-size: 18px; font-weight: 600; }
.primary { background: #147f70; color: white; border-radius: 10px; font-weight: 700; }
.danger { background: #5b2630; color: #ffdfe4; border-radius: 10px; }
.navbtn { min-height: 42px; border-radius: 10px; }
.status-good { color: #6fe1c6; font-weight: 700; }
.status-warn { color: #f2bd69; font-weight: 700; }
textview { background: #0e1a2b; color: #dce8f7; border-radius: 10px; }
"""

LIGHT_CSS = r"""
window { background: #f3f6f9; color: #173047; }
.sidebar { background: #ffffff; border: 1px solid #d7e0e8; border-radius: 18px; padding: 18px; }
.card { background: #ffffff; border: 1px solid #d7e0e8; border-radius: 16px; padding: 18px; }
.soft { background: #eaf1f5; border-radius: 12px; padding: 12px; }
.title-big { font-size: 28px; font-weight: 700; color: #173047; }
.brand { font-size: 30px; font-weight: 800; color: #147f70; }
.muted { color: #5b7185; }
.metric { font-size: 18px; font-weight: 600; }
.primary { background: #147f70; color: white; border-radius: 10px; font-weight: 700; }
.danger { background: #f4d9dd; color: #5b2630; border-radius: 10px; }
.navbtn { min-height: 42px; border-radius: 10px; }
.status-good { color: #147f70; font-weight: 700; }
.status-warn { color: #9a6519; font-weight: 700; }
textview { background: #f7fafc; color: #173047; border-radius: 10px; }
"""

def label(text="", css=None, xalign=1.0, wrap=True):
    w = Gtk.Label(label=text)
    w.set_xalign(xalign)
    w.set_wrap(wrap)
    if css:
        w.add_css_class(css)
    return w

def button(text, callback=None, css=None):
    b = Gtk.Button(label=text)
    b.add_css_class("navbtn")
    if css:
        b.add_css_class(css)
    if callback:
        b.connect("clicked", callback)
    return b

def card():
    b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    b.add_css_class("card")
    return b

def hbox(spacing=8):
    return Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=spacing)

def vbox(spacing=10):
    return Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)

class FreeNetHub(Adw.Application):
    def __init__(self):
        super().__init__(application_id="local.freenethub")
        self.win = None
        self.css_provider = None
        self.dark = True
        self.pending_warp_token = None
        self.last_result = {}
        self.monitor_failures = 0
        self.repairs = 0
        self.busy = False

    def do_activate(self):
        if self.win:
            self.win.present()
            return

        Gtk.Widget.set_default_direction(Gtk.TextDirection.RTL)
        self.apply_theme(True)

        self.win = Adw.ApplicationWindow(application=self)
        self.win.set_title(f"FreeNet Hub {core.VERSION}")
        self.win.set_default_size(1180, 800)
        self.win.set_size_request(880, 620)
        self.win.set_decorated(True)
        self.win.set_modal(False)

        # Libadwaita requires HeaderBar to live inside a ToolbarView.
        # The previous build had no native window controls.
        titlebar = Adw.HeaderBar()
        titlebar.set_show_start_title_buttons(False)
        titlebar.set_show_end_title_buttons(False)

        title = Gtk.Label(label=f"FreeNet Hub · {core.VERSION}")
        title.add_css_class("heading")
        titlebar.set_title_widget(title)

        minimize_btn = Gtk.Button()
        minimize_btn.set_icon_name("window-minimize-symbolic")
        minimize_btn.set_tooltip_text("کوچک کردن")
        minimize_btn.connect("clicked", lambda *_: self.win.minimize())

        maximize_btn = Gtk.Button()
        maximize_btn.set_icon_name("window-maximize-symbolic")
        maximize_btn.set_tooltip_text("بزرگ / بازگرداندن")
        maximize_btn.connect("clicked", self.toggle_maximize)

        close_btn = Gtk.Button()
        close_btn.set_icon_name("window-close-symbolic")
        close_btn.set_tooltip_text("بستن")
        close_btn.add_css_class("destructive-action")
        close_btn.connect("clicked", lambda *_: self.win.close())

        titlebar.pack_end(close_btn)
        titlebar.pack_end(maximize_btn)
        titlebar.pack_end(minimize_btn)
        self.window_header = titlebar
        self.minimize_button = minimize_btn
        self.maximize_button = maximize_btn
        self.close_button = close_btn

        root = hbox(18)
        root.set_margin_top(18)
        root.set_margin_bottom(18)
        root.set_margin_start(18)
        root.set_margin_end(18)

        main = vbox(14)
        main.set_hexpand(True)
        root.append(main)

        sidebar = self.build_sidebar()
        sidebar.set_size_request(230, -1)
        root.append(sidebar)

        head = hbox(12)
        titlebox = vbox(2)
        titlebox.set_hexpand(True)
        titlebox.append(label("اتصال، با کنترل و شفافیت", "title-big"))
        titlebox.append(label("مسیر مناسب را انتخاب کن؛ نتیجهٔ واقعی را ببین.", "muted"))
        head.append(titlebox)
        badge = label("LINUX · DESKTOP + GATEWAY", "muted", xalign=0.5)
        badge.add_css_class("soft")
        head.append(badge)
        main.append(head)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_vexpand(True)
        self.stack.add_named(self.build_connect_page(), "connect")
        self.stack.add_named(self.build_gateway_page(), "gateway")
        self.stack.add_named(self.build_resilience_page(), "resilience")
        self.stack.add_named(self.build_tools_page(), "tools")
        self.stack.add_named(self.build_about_page(), "about")
        main.append(self.stack)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(titlebar)
        toolbar.set_content(root)
        self.win.set_content(toolbar)
        self.win.present()
        self.refresh_snapshot()
        GLib.timeout_add_seconds(45, self.monitor_tick)

    def toggle_maximize(self, *_):
        if self.win.is_maximized():
            self.win.unmaximize()
        else:
            self.win.maximize()

    def apply_theme(self, dark):
        self.dark = dark
        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK if dark else Adw.ColorScheme.FORCE_LIGHT
        )
        provider = Gtk.CssProvider()
        provider.load_from_data((DARK_CSS if dark else LIGHT_CSS).encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.css_provider = provider

    def build_sidebar(self):
        box = vbox(10)
        box.add_css_class("sidebar")
        box.append(label("FREENET", "brand", xalign=0.0))
        box.append(label("HUB / 4.2 LINUX", "muted", xalign=0.0))

        state = vbox(5)
        state.add_css_class("soft")
        self.sidebar_state = label("آماده", xalign=1.0)
        self.sidebar_state.add_css_class("metric")
        self.sidebar_detail = label("باز شدن برنامه هیچ اتصال شبکه‌ای را روشن نمی‌کند.", "muted")
        state.append(self.sidebar_state)
        state.append(self.sidebar_detail)
        box.append(state)

        box.append(button("اتصال هوشمند", lambda *_: self.connect("AUTO"), "primary"))
        box.append(button("قطع اتصال‌های FreeNet Hub", lambda *_: self.run_async("Stop", core.stop_all), "danger"))

        sep = Gtk.Separator()
        sep.set_margin_top(8)
        sep.set_margin_bottom(8)
        box.append(sep)

        for text, page, icon in [
            ("اتصال", "connect", "network-vpn-symbolic"),
            ("گیت‌وی", "gateway", "network-wired-symbolic"),
            ("تاب‌آوری", "resilience", "security-high-symbolic"),
            ("ابزارها", "tools", "applications-system-symbolic"),
            ("درباره", "about", "help-about-symbolic"),
        ]:
            b = Gtk.Button()
            row = hbox(8)
            img = Gtk.Image.new_from_icon_name(icon)
            row.append(img)
            row.append(label(text, xalign=1.0))
            b.set_child(row)
            b.add_css_class("navbtn")
            b.connect("clicked", lambda _b, p=page: self.stack.set_visible_child_name(p))
            box.append(b)

        box.append(Gtk.Separator())
        box.append(button("روشن / تیره", self.toggle_theme))
        footer = label("یک مرکز کنترل\nبدون ترمینال اضافی\nبدون اتصال خودکار", "muted")
        footer.set_vexpand(True)
        footer.set_valign(Gtk.Align.END)
        box.append(footer)
        return box

    def build_connect_page(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        root = vbox(14)
        root.set_margin_top(4)
        root.set_margin_bottom(12)
        scroll.set_child(root)

        status = card()
        self.status_title = label("در حال خواندن وضعیت", "title-big")
        self.status_detail = label("—", "muted")
        status.append(self.status_title)
        status.append(self.status_detail)

        metrics = hbox(12)
        metrics.set_homogeneous(True)
        for title, attr in [
            ("مسیر", "route_value"),
            ("کشور گزارش‌شده", "country_value"),
            ("WARP", "warp_value"),
        ]:
            m = vbox(4)
            m.add_css_class("soft")
            m.append(label(title, "muted"))
            v = label("—", "metric")
            setattr(self, attr, v)
            m.append(v)
            metrics.append(m)
        status.append(metrics)

        iprow = hbox(10)
        iprow.append(label("IP:", "muted"))
        self.ip_value = label("پنهان", xalign=0.0)
        self.ip_value.set_selectable(True)
        self.ip_value.set_hexpand(True)
        self.show_ip = Gtk.Switch()
        self.show_ip.connect("notify::active", lambda *_: self.refresh_snapshot())
        iprow.append(self.ip_value)
        iprow.append(label("نمایش IP", "muted"))
        iprow.append(self.show_ip)
        status.append(iprow)
        root.append(status)

        controls = card()
        controls.append(label("حالت اتصال", "metric"))
        mode_row = hbox(10)
        self.mode = Gtk.DropDown.new_from_strings([
            "AUTO · هوشمند",
            "WARP · کل سیستم",
            "TOR · مستقیم",
            "OBFS4 · Tor مقاوم",
            "SNOWFLAKE · Tor Snowflake",
            "DIRECT · بدون تونل",
        ])
        self.mode.set_selected(0)
        self.mode.set_hexpand(True)
        mode_row.append(self.mode)
        mode_row.append(button("شروع اتصال", lambda *_: self.connect(self.selected_mode()), "primary"))
        controls.append(mode_row)

        acts = hbox(8)
        acts.append(button("باز کردن مرورگر", lambda *_: self.run_async("Browser", core.open_browser)))
        acts.append(button("بررسی مسیر", lambda *_: self.run_async("Verify", core.verify_current)))
        self.keep_btn = button("نگه‌داشتن WARP", self.keep_warp)
        self.keep_btn.set_sensitive(False)
        acts.append(self.keep_btn)
        acts.append(button("توقف", lambda *_: self.run_async("Stop", core.stop_all), "danger"))
        controls.append(acts)
        controls.append(label(
            "WARP ابتدا به‌صورت trial امن وصل می‌شود و اگر تأیید نشود خودکار قطع می‌شود. "
            "Tor و obfs4 فقط پروکسی اختصاصی FreeNet Hub را مدیریت می‌کنند.", "muted"
        ))
        root.append(controls)

        monitor = card()
        monitor.append(label("پایایی اختیاری", "metric"))
        mr = hbox(14)
        self.monitor_switch = Gtk.Switch()
        self.repair_switch = Gtk.Switch()
        mr.append(label("بررسی هر ۴۵ ثانیه", "muted"))
        mr.append(self.monitor_switch)
        mr.append(label("بازیابی محدود Tor پس از ۳ شکست", "muted"))
        mr.append(self.repair_switch)
        monitor.append(mr)
        self.monitor_label = label("پیش‌فرض خاموش؛ هیچ reset سیستم یا تغییر DNS انجام نمی‌شود.", "muted")
        monitor.append(self.monitor_label)
        root.append(monitor)
        return scroll

    def build_gateway_page(self):
        scroll = Gtk.ScrolledWindow()
        root = vbox(14)
        root.set_margin_top(4)
        root.set_margin_bottom(12)
        scroll.set_child(root)

        intro = card()
        intro.append(label("گیت‌وی دوحالته", "title-big"))
        intro.append(label(
            "حالت اول تونل کل لپ‌تاپ با WARP است. حالت دوم یک شبکهٔ اختصاصی Wi‑Fi برای کنسول آماده می‌کند. "
            "هیچ‌کدام هنگام بازشدن برنامه خودکار فعال نمی‌شوند.", "muted"
        ))

        cards = hbox(12)
        cards.set_homogeneous(True)

        pc = vbox(10)
        pc.add_css_class("soft")
        pc.append(label("کل کامپیوتر", "metric"))
        pc.append(label("تمام ترافیک میزبان از WARP عبور می‌کند؛ trial امن و rollback خودکار فعال است.", "muted"))
        pc.append(button("روشن کردن تونل PC", lambda *_: self.connect("WARP"), "primary"))
        pc.append(button("قطع تونل PC", lambda *_: self.run_async("WARP Stop", core.warp_disconnect)))
        cards.append(pc)

        con = vbox(10)
        con.add_css_class("soft")
        con.append(label("کنسول / Hotspot", "metric"))
        con.append(label("Wi‑Fi آزاد لپ‌تاپ به شبکهٔ 192.168.77.0/24 تبدیل می‌شود؛ WARP باید قبلاً تأیید شده باشد.", "muted"))
        con.append(button("آماده‌سازی کنسول", self.confirm_console_prepare))
        con.append(button("روشن کردن Hotspot", self.confirm_console_start, "primary"))
        con.append(button("خاموش کردن Hotspot", lambda *_: self.run_async("Console Stop", core.console_stop)))
        cards.append(con)

        intro.append(cards)
        self.gateway_state = label("در حال بررسی…", "muted")
        intro.append(self.gateway_state)
        intro.append(button("تازه‌سازی وضعیت", lambda *_: self.run_async("Gateway Status", core.console_status)))
        root.append(intro)

        safety = card()
        safety.append(label("اصل ایمنی", "metric"))
        safety.append(label(
            "اگر WARP، route یا rollback تأیید نشود حالت فعال پذیرفته نمی‌شود. "
            "اعتبارسنجی فیزیکی کنسول (DHCP/UDP/کشور بازی) فقط بعد از اتصال دستگاه واقعی PASS خواهد شد.", "muted"
        ))
        root.append(safety)
        return scroll

    def build_resilience_page(self):
        scroll = Gtk.ScrolledWindow()
        root = vbox(14)
        root.set_margin_top(4)
        root.set_margin_bottom(12)
        scroll.set_child(root)

        c = card()
        c.append(label("مسیر جایگزین واقعی", "title-big"))
        c.append(label(
            "WARP و Tor دو خانوادهٔ متفاوت‌اند. مسیرهای Tor شامل مستقیم، obfs4 و Snowflake هستند و در نبود material معتبر fail-closed می‌مانند.", "muted"
        ))
        row = hbox(8)
        row.append(button("Tor مستقیم", lambda *_: self.run_async("Tor Direct", lambda: core.start_tor("direct"))))
        row.append(button("Tor obfs4", lambda *_: self.run_async("Tor obfs4", lambda: core.start_tor("obfs4"))))
        row.append(button("Tor Snowflake", lambda *_: self.run_async("Tor Snowflake", lambda: core.start_tor("snowflake"))))
        row.append(button("توقف Tor", lambda *_: self.run_async("Tor Stop", core.stop_tor), "danger"))
        c.append(row)
        self.bridge_state = label(f"پل‌های obfs4: {len(core.bridge_lines(core.BRIDGES))} · Snowflake: {len(core.bridge_lines(core.SNOWFLAKE_BRIDGES))}", "muted")
        c.append(self.bridge_state)
        imports = hbox(8)
        imports.append(button("وارد کردن فایل obfs4", self.import_bridges))
        imports.append(button("وارد کردن فایل Snowflake", self.import_snowflake))
        c.append(imports)
        root.append(c)

        policy = card()
        policy.append(label("Fail‑closed", "metric"))
        policy.append(label(
            "پل ساختگی یا WebTunnel نامعتبر وارد نمی‌شود. اگر bridge معتبر، executable یا HTTPS egress موجود نباشد، "
            "FreeNet Hub مسیر را سالم اعلام نمی‌کند.", "muted"
        ))
        root.append(policy)
        return scroll

    def build_tools_page(self):
        root = vbox(12)
        row = hbox(8)
        for text, name, fn in [
            ("موجودی", "Inventory", core.inventory),
            ("Doctor", "Doctor", core.doctor),
            ("سرعت 2MB", "Speed", core.speed_sample),
            ("نسخه‌ها", "Updates", core.update_status),
            ("گزارش پالایش‌شده", "Export", core.export_report),
        ]:
            row.append(button(text, lambda _b, n=name, f=fn: self.run_async(n, f)))
        root.append(row)

        self.details = Gtk.TextView()
        self.details.set_editable(False)
        self.details.set_monospace(True)
        self.details.set_direction(Gtk.TextDirection.LTR)
        self.details.get_buffer().set_text("No operation has started. Opening the app does not connect.")
        sc = Gtk.ScrolledWindow()
        sc.set_vexpand(True)
        sc.set_child(self.details)
        root.append(sc)

        br = hbox(8)
        br.append(button("کپی نتیجه", self.copy_details))
        br.append(button("باز کردن پوشه شواهد", self.open_evidence))
        root.append(br)
        return root

    def build_about_page(self):
        root = vbox(14)
        c = card()
        c.append(label("FreeNet Hub", "brand", xalign=0.5))
        c.append(label(core.VERSION, "muted", xalign=0.5))
        c.append(label(
            "مرکز کنترل اتصال برای Linux با GTK4/Libadwaita، WARP رسمی، Tor و obfs4. "
            "هدف طراحی: کنترل صریح، rollback قابل اثبات، بدون ترمینال اضافی و بدون دست‌کاری شبکه هنگام اجرای برنامه.",
            xalign=0.5,
        ))
        c.append(label(
            "قابلیت Console Gateway تا زمان آزمون با دستگاه واقعی، Software Ready / Physical Validation Open باقی می‌ماند.",
            "muted",
            xalign=0.5,
        ))
        root.append(c)
        return root

    def selected_mode(self):
        values = ["AUTO", "WARP", "TOR", "OBFS4", "SNOWFLAKE", "DIRECT"]
        return values[self.mode.get_selected()]

    def set_busy(self, value, text=None):
        self.busy = value
        if text:
            self.sidebar_state.set_text(text)

    def run_async(self, name, fn, on_done=None):
        if self.busy:
            return
        self.set_busy(True, f"در حال اجرا: {name}")
        self.status_detail.set_text(f"در حال انجام {name}…")

        def worker():
            try:
                result = fn()
            except Exception as e:
                result = {"ok": False, "error": repr(e)}
            GLib.idle_add(self.finish_action, name, result, on_done)

        threading.Thread(target=worker, daemon=True).start()

    def finish_action(self, name, result, on_done):
        self.set_busy(False)
        self.last_result = result or {}
        text = json.dumps(result, ensure_ascii=False, indent=2)
        self.details.get_buffer().set_text(text)
        ok = bool(result and result.get("ok"))
        self.sidebar_state.set_text("موفق" if ok else "نیاز به توجه")
        self.sidebar_detail.set_text(name)
        if result and result.get("guard", {}).get("token"):
            self.pending_warp_token = result["guard"]["token"]
            self.keep_btn.set_sensitive(True)
            self.status_detail.set_text(
                f"WARP وصل است؛ برای دائمی‌کردن تا {core.WARP_GUARD_SECONDS} ثانیه «نگه‌داشتن WARP» را بزنید."
            )
        elif result and result.get("needs_keep") is False and result.get("warp") == "on":
            self.pending_warp_token = None
            self.keep_btn.set_sensitive(False)
        if on_done:
            on_done(result)
        self.refresh_snapshot()
        if name.startswith("Console") or name == "Gateway Status":
            self.update_gateway_text(result)
        return False

    def connect(self, mode):
        self.run_async("Connect " + mode, lambda: core.connect_mode(mode))

    def keep_warp(self, *_):
        if not self.pending_warp_token:
            self.status_detail.set_text("trial فعالی برای نگه‌داشتن وجود ندارد.")
            return
        token = self.pending_warp_token
        def done(result):
            if result.get("ok"):
                self.pending_warp_token = None
                self.keep_btn.set_sensitive(False)
        self.run_async("Keep WARP", lambda: core.warp_keep(token), done)

    def refresh_snapshot(self):
        try:
            s = core.app_snapshot()
            mode = s.get("mode") or "—"
            provider = s.get("provider") or "—"
            country = s.get("country") or "—"
            warp = s.get("warp") or ("on" if mode in ("WARP", "WARP_TRIAL") and s.get("ok") else "off")
            self.route_value.set_text(provider)
            self.country_value.set_text("Tor / نامشخص" if country == "T1" else country)
            self.warp_value.set_text(warp)
            self.ip_value.set_text((s.get("ip") or "—") if self.show_ip.get_active() else "پنهان")
            if s.get("ok") and s.get("mode"):
                self.status_title.set_text("مسیر تأیید شد")
                self.status_title.remove_css_class("status-warn")
                self.status_title.add_css_class("status-good")
                self.status_detail.set_text(f"حالت فعال: {mode} · Provider: {provider}")
                self.sidebar_state.set_text("متصل")
            elif not s.get("mode"):
                self.status_title.set_text("آمادهٔ انتخاب مسیر")
                self.status_detail.set_text("باز شدن برنامه هیچ VPN یا proxy را روشن نمی‌کند.")
                self.sidebar_state.set_text("آماده")
            else:
                self.status_title.set_text("مسیر نیاز به بررسی دارد")
                self.status_title.add_css_class("status-warn")
        except Exception as e:
            self.status_title.set_text("خواندن وضعیت ناموفق")
            self.status_detail.set_text(str(e))

    def update_gateway_text(self, result):
        if not result:
            return
        if result.get("config") and result.get("state") == "prepared":
            c = result["config"]
            private_cfg = core.load_json(core.CONSOLE, {})
            password = private_cfg.get("password") or "ناموجود"
            self.gateway_state.set_text(
                f"آماده: SSID={c.get('ssid')} · Password={password} · Gateway={c.get('gateway')} · "
                "اعتبارسنجی فیزیکی هنوز باز است."
            )
        elif result.get("state") == "hotspot-up":
            self.gateway_state.set_text("Hotspot کنسول روشن است؛ آزمون با کنسول واقعی هنوز لازم است.")
        elif result.get("candidates") is not None:
            names = ", ".join(x.get("device", "") for x in result.get("candidates", [])) or "هیچ‌کدام"
            self.gateway_state.set_text(f"Uplink: {result.get('uplink')} · آداپتورهای ثانویه: {names}")
        elif result.get("error"):
            self.gateway_state.set_text("خطا: " + str(result.get("error")))

    def confirm_console_prepare(self, *_):
        self.confirm(
            "آماده‌سازی شبکهٔ کنسول",
            "یک connection محلی NetworkManager با نام FreeNetHub-Console ساخته می‌شود؛ هنوز روشن نمی‌شود. ادامه؟",
            lambda: self.run_async("Console Prepare", core.console_prepare),
        )

    def confirm_console_start(self, *_):
        self.confirm(
            "روشن کردن Hotspot کنسول",
            "WARP باید واقعاً روشن باشد. Hotspot محلی فعال می‌شود؛ اعتبارسنجی فیزیکی بازی همچنان جداست. ادامه؟",
            lambda: self.run_async("Console Start", core.console_start),
        )

    def confirm(self, title, text, yes_cb):
        d = Gtk.MessageDialog(
            transient_for=self.win,
            modal=True,
            buttons=Gtk.ButtonsType.YES_NO,
            message_type=Gtk.MessageType.QUESTION,
            text=title,
            secondary_text=text,
        )
        def response(dialog, resp):
            dialog.destroy()
            if resp == Gtk.ResponseType.YES:
                yes_cb()
        d.connect("response", response)
        d.present()

    def import_bridges(self, *_):
        chooser = Gtk.FileChooserNative.new(
            "انتخاب فایل obfs4", self.win, Gtk.FileChooserAction.OPEN, "انتخاب", "لغو"
        )
        def response(d, resp):
            if resp == Gtk.ResponseType.ACCEPT:
                f = d.get_file()
                if f:
                    self.run_async(
                        "Import obfs4",
                        lambda: core.import_obfs4(f.get_path()),
                        lambda r: self.refresh_bridge_state() if r.get("ok") else None,
                    )
            d.destroy()
        chooser.connect("response", response)
        chooser.show()

    def refresh_bridge_state(self):
        self.bridge_state.set_text(
            f"پل‌های obfs4: {len(core.bridge_lines(core.BRIDGES))} · Snowflake: {len(core.bridge_lines(core.SNOWFLAKE_BRIDGES))}"
        )

    def import_snowflake(self, *_):
        chooser = Gtk.FileChooserNative.new(
            "انتخاب فایل Snowflake", self.win, Gtk.FileChooserAction.OPEN, "انتخاب", "لغو"
        )
        def response(d, resp):
            if resp == Gtk.ResponseType.ACCEPT:
                f = d.get_file()
                if f:
                    self.run_async(
                        "Import Snowflake",
                        lambda: core.import_snowflake(f.get_path()),
                        lambda r: self.refresh_bridge_state() if r.get("ok") else None,
                    )
            d.destroy()
        chooser.connect("response", response)
        chooser.show()

    def monitor_tick(self):
        if not self.monitor_switch.get_active() or self.busy:
            return True
        def worker():
            try:
                r = core.verify_current()
            except Exception as e:
                r = {"ok": False, "error": repr(e)}
            GLib.idle_add(self.monitor_done, r)
        threading.Thread(target=worker, daemon=True).start()
        return True

    def monitor_done(self, result):
        if result.get("ok"):
            self.monitor_failures = 0
            self.monitor_label.set_text("آخرین بررسی: موفق")
            self.refresh_snapshot()
            return False
        self.monitor_failures += 1
        self.monitor_label.set_text(f"شکست متوالی: {self.monitor_failures}")
        if self.monitor_failures >= 3 and self.repair_switch.get_active() and self.repairs < 2:
            s = core.session()
            if s.get("mode") == "TOR":
                self.repairs += 1
                self.monitor_failures = 0
                self.run_async("Tor Auto Repair", core.start_tor)
            elif s.get("mode") in ("WARP", "WARP_TRIAL"):
                self.monitor_label.set_text("WARP نیاز به اقدام کاربر دارد؛ auto-repair سیستم‌گسترده عمداً اجرا نشد.")
        return False

    def toggle_theme(self, *_):
        self.apply_theme(not self.dark)

    def copy_details(self, *_):
        buf = self.details.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        clip = Gdk.Display.get_default().get_clipboard()
        clip.set(text)

    def open_evidence(self, *_):
        core.ensure_dirs()
        subprocess.Popen(["xdg-open", str(core.EVIDENCE)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    core.ensure_dirs()
    raise SystemExit(FreeNetHub().run(sys.argv))
