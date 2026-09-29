#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import threading

import gi
gi.require_version("Gtk","4.0")
gi.require_version("Adw","1")
from gi.repository import Adw,Gdk,GLib,Gtk

import freenet_hub_linux as legacy
import freenet_hub_linux_r37 as core

ACCENT="#39cdb4"

DARK_CSS=r"""
window { background:#08111f; color:#edf5ff; }
.sidebar { background:#101f33; border:1px solid #243b55; border-radius:18px; padding:16px; }
.card { background:#101f33; border:1px solid #29435f; border-radius:16px; padding:16px; }
.card-selected { background:#11344c; border:2px solid #39cdb4; }
.soft { background:#172c43; border-radius:11px; padding:10px; }
.brand { color:#39cdb4; font-size:28px; font-weight:800; }
.title-big { font-size:27px; font-weight:800; }
.section-title { font-size:20px; font-weight:750; }
.metric { font-size:17px; font-weight:700; }
.muted { color:#9eb3ca; }
.good { color:#66e2c6; font-weight:700; }
.warn { color:#f2bd69; font-weight:700; }
.bad { color:#ff8895; font-weight:700; }
.primary { background:#147f70; color:white; border-radius:10px; font-weight:700; }
.danger { background:#5a2430; color:#ffe4e8; border-radius:10px; }
.scope { min-height:46px; border-radius:11px; }
.navbtn { min-height:42px; border-radius:10px; }
.method-title { font-size:17px; font-weight:750; }
.pill { background:#17334a; border-radius:999px; padding:4px 8px; }
entry, dropdown, spinbutton { min-height:36px; }
textview { background:#0b1728; color:#dceafd; border-radius:10px; }
listbox { background:transparent; }
.node-row { background:#101f33; border:1px solid #29435f; border-radius:10px; padding:8px; margin:3px 0; }
"""

LIGHT_CSS=r"""
window { background:#f2f6f9; color:#173047; }
.sidebar { background:#ffffff; border:1px solid #d5e0e8; border-radius:18px; padding:16px; }
.card { background:#ffffff; border:1px solid #d5e0e8; border-radius:16px; padding:16px; }
.card-selected { background:#e8f7f4; border:2px solid #147f70; }
.soft { background:#e9f0f5; border-radius:11px; padding:10px; }
.brand { color:#147f70; font-size:28px; font-weight:800; }
.title-big { font-size:27px; font-weight:800; }
.section-title { font-size:20px; font-weight:750; }
.metric { font-size:17px; font-weight:700; }
.muted { color:#5f7488; }
.good { color:#147f70; font-weight:700; }
.warn { color:#9a6519; font-weight:700; }
.bad { color:#a42f3f; font-weight:700; }
.primary { background:#147f70; color:white; border-radius:10px; font-weight:700; }
.danger { background:#f3d8dd; color:#6b2530; border-radius:10px; }
.scope { min-height:46px; border-radius:11px; }
.navbtn { min-height:42px; border-radius:10px; }
.method-title { font-size:17px; font-weight:750; }
.pill { background:#e4eef3; border-radius:999px; padding:4px 8px; }
entry, dropdown, spinbutton { min-height:36px; }
textview { background:#f7fafc; color:#173047; border-radius:10px; }
listbox { background:transparent; }
.node-row { background:#ffffff; border:1px solid #d5e0e8; border-radius:10px; padding:8px; margin:3px 0; }
"""

METHODS=[
    ("AUTO","هوشمند","Node / Tor با fallback امن","مرورگر ✓ · کل سیستم WARP"),
    ("NODE","Node Pool","VLESS / VMess / SS / Trojan / Hysteria2","مرورگر ✓ · سیستم نیازمند helper"),
    ("WARP","WARP","Cloudflare WARP رسمی","کل سیستم ✓"),
    ("TOR","Tor / Bridges","Direct / obfs4 / Snowflake","مرورگر ✓"),
    ("CUSTOM","Custom Proxy","HTTP / SOCKS شخصی","مرورگر ✓"),
    ("DIRECT","Direct","مسیر فعلی سیستم بدون تونل","پایه سیستم"),
    ("GOOL","GOOL","warp-plus · Warp-in-Warp","مرورگر ✓"),
    ("CFON","CFON","warp-plus · Psiphon country mode","مرورگر ✓"),
]

def label(text="",css=None,xalign=1.0,wrap=True):
    w=Gtk.Label(label=text)
    w.set_xalign(xalign);w.set_wrap(wrap)
    if css:w.add_css_class(css)
    return w

def button(text,cb=None,css=None):
    b=Gtk.Button(label=text);b.add_css_class("navbtn")
    if css:b.add_css_class(css)
    if cb:b.connect("clicked",cb)
    return b

def hbox(spacing=8):
    return Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=spacing)

def vbox(spacing=10):
    return Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=spacing)

def card():
    b=vbox(10);b.add_css_class("card");return b

def scroll(child):
    s=Gtk.ScrolledWindow();s.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);s.set_child(child);return s

class FreeNetHub(Adw.Application):
    def __init__(self):
        super().__init__(application_id="local.freenethub")
        self.win=None
        self.stack=None
        self.busy=False
        self.dark=core.settings().get("theme")=="dark"
        self.scope="BROWSER"
        self.method="AUTO"
        self.pending_warp_token=None
        self.metrics={}
        self.node_cache=[]
        self.selected_node_id=""
        self.nav={}
        self.method_cards={}
        self.method_metric={}
        self.compare_metric={}
        self.monitor_failures=0
        self.repairs=0

    def do_activate(self):
        if self.win:
            self.win.present();return
        Gtk.Widget.set_default_direction(Gtk.TextDirection.RTL)
        self.apply_theme(self.dark)

        self.win=Adw.ApplicationWindow(application=self)
        self.win.set_title(f"FreeNet Hub · {core.VERSION}")
        self.win.set_default_size(1360,860)
        self.win.set_size_request(1020,680)

        hb=Adw.HeaderBar()
        hb.set_show_start_title_buttons(False);hb.set_show_end_title_buttons(False)
        hb.set_title_widget(label(f"FreeNet Hub · {core.VERSION}","metric",xalign=.5))
        for icon,tip,cb in [
            ("window-close-symbolic","بستن",lambda *_:self.win.close()),
            ("window-maximize-symbolic","بزرگ / بازگرداندن",self.toggle_maximize),
            ("window-minimize-symbolic","کوچک کردن",lambda *_:self.win.minimize()),
        ]:
            b=Gtk.Button();b.set_icon_name(icon);b.set_tooltip_text(tip);b.connect("clicked",cb);hb.pack_end(b)

        outer=hbox(16);outer.set_margin_top(14);outer.set_margin_bottom(14);outer.set_margin_start(14);outer.set_margin_end(14)
        main=vbox(12);main.set_hexpand(True)
        outer.append(main)
        side=self.build_sidebar();side.set_size_request(245,-1);outer.append(side)

        self.stack=Gtk.Stack();self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE);self.stack.set_vexpand(True)
        self.stack.add_named(self.build_dashboard(),"dashboard")
        self.stack.add_named(self.build_methods(),"methods")
        self.stack.add_named(self.build_nodes(),"nodes")
        self.stack.add_named(self.build_tools(),"tools")
        self.stack.add_named(self.build_settings(),"settings")
        main.append(self.stack)

        toolbar=Adw.ToolbarView();toolbar.add_top_bar(hb);toolbar.set_content(outer)
        self.win.set_content(toolbar)
        self.show_page("dashboard")
        self.win.present()
        self.refresh_all()
        GLib.timeout_add_seconds(20,self.periodic_refresh)

    def toggle_maximize(self,*_):
        self.win.unmaximize() if self.win.is_maximized() else self.win.maximize()

    def apply_theme(self,dark):
        self.dark=bool(dark)
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK if self.dark else Adw.ColorScheme.FORCE_LIGHT)
        p=Gtk.CssProvider();p.load_from_data((DARK_CSS if self.dark else LIGHT_CSS).encode())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),p,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.css_provider=p

    def build_sidebar(self):
        b=vbox(9);b.add_css_class("sidebar")
        b.append(label("FREENET","brand",xalign=0.0));b.append(label("HUB · R37 LINUX","muted",xalign=0.0))
        state=vbox(3);state.add_css_class("soft")
        self.sidebar_state=label("آماده","metric");self.sidebar_detail=label("بدون اتصال خودکار","muted")
        state.append(self.sidebar_state);state.append(self.sidebar_detail);b.append(state)

        q=hbox(6);q.append(button("اتصال",lambda *_:self.connect_selected(),"primary"));q.append(button("توقف",lambda *_:self.run_async("Stop",core.stop_all),"danger"));b.append(q)
        b.append(Gtk.Separator())
        for text,name,icon in [
            ("داشبورد","dashboard","view-grid-symbolic"),
            ("روش‌ها","methods","network-vpn-symbolic"),
            ("نودها","nodes","network-server-symbolic"),
            ("ابزارها","tools","applications-system-symbolic"),
            ("تنظیمات","settings","preferences-system-symbolic"),
        ]:
            x=Gtk.Button();row=hbox(8);row.append(Gtk.Image.new_from_icon_name(icon));row.append(label(text,xalign=1.0));x.set_child(row);x.add_css_class("navbtn");x.connect("clicked",lambda _b,n=name:self.show_page(n));b.append(x);self.nav[name]=x
        b.append(Gtk.Separator())
        self.sidebar_scope=label("Scope: مرورگر","muted");b.append(self.sidebar_scope)
        self.sidebar_method=label("Method: هوشمند","muted");b.append(self.sidebar_method)
        f=label("Explicit connect · Fail-closed\nNo terminal window · No auto VPN","muted");f.set_vexpand(True);f.set_valign(Gtk.Align.END);b.append(f)
        return b

    def page_head(self,title,subtitle):
        h=vbox(2);h.append(label(title,"title-big"));h.append(label(subtitle,"muted"));return h

    def build_dashboard(self):
        root=vbox(12);root.set_margin_bottom(12);root.append(self.page_head("داشبورد","اتصال، تست و وضعیت در یک نگاه"))

        status=card()
        top=hbox(10);st=vbox(2);st.set_hexpand(True)
        self.status_title=label("در حال خواندن وضعیت","section-title");self.status_detail=label("—","muted")
        st.append(self.status_title);st.append(self.status_detail);top.append(st)
        self.quick_browser=button("باز کردن مرورگر",lambda *_:self.run_async("Browser",core.open_browser));top.append(self.quick_browser)
        status.append(top)

        metrics=hbox(8);metrics.set_homogeneous(True)
        for title,attr in [("مسیر","dash_route"),("کشور","dash_country"),("WARP","dash_warp"),("IP","dash_ip"),("Ping","dash_ping")]:
            m=vbox(2);m.add_css_class("soft");m.append(label(title,"muted"));v=label("—","metric");setattr(self,attr,v);m.append(v);metrics.append(m)
        status.append(metrics)
        root.append(status)

        scopes=card();scopes.append(label("نوع اتصال","section-title"))
        row=hbox(8);row.set_homogeneous(True)
        for key,text,sub in [
            ("BROWSER","◎  مرورگر","پیش‌فرض امن؛ فقط برنامه/پروفایل FreeNet Hub"),
            ("SYSTEM","▣  کل سیستم","WARP رسمی؛ mutation فقط با اقدام صریح"),
            ("CONSOLE",">_  کنسول","Gateway مستقل؛ مسیر کل سیستم دست‌نخورده"),
        ]:
            b=Gtk.ToggleButton();inner=vbox(2);inner.append(label(text,"metric",xalign=.5));inner.append(label(sub,"muted",xalign=.5));b.set_child(inner);b.add_css_class("scope");b.connect("clicked",lambda x,k=key:self.set_scope(k,x));row.append(b);setattr(self,"scope_"+key.lower(),b)
        scopes.append(row);root.append(scopes)

        choose=card()
        ch=hbox(8);txt=vbox(2);txt.set_hexpand(True);txt.append(label("روش اتصال","section-title"));txt.append(label("کارت را انتخاب کن؛ تست قبل از اتصال مستقل است.","muted"));ch.append(txt)
        ch.append(button("همه روش‌ها",lambda *_:self.show_page("methods")));choose.append(ch)
        cards=Gtk.Grid(column_spacing=8,row_spacing=8)
        for idx,key in enumerate(["AUTO","NODE","WARP","TOR","DIRECT"]):
            title,desc,cap=next((x[1],x[2],x[3]) for x in METHODS if x[0]==key)
            c=self.method_card(key,title,desc,cap,compact=True);cards.attach(c,idx%5,idx//5,1,1)
        choose.append(cards);root.append(choose)

        act=card();act.append(label("اقدام","section-title"))
        ar=hbox(8);ar.set_homogeneous(True)
        ar.append(button("⌁  تست Ping",lambda *_:self.test_selected(True)))
        ar.append(button("✓  Ping + Download + Upload",lambda *_:self.test_selected(False),"primary"))
        ar.append(button("▶  اتصال",lambda *_:self.connect_selected(),"primary"))
        self.keep_btn=button("نگه‌داشتن WARP",self.keep_warp);self.keep_btn.set_sensitive(False);ar.append(self.keep_btn)
        act.append(ar);root.append(act)

        cmp=card();cmp.append(label("مقایسه آخرین نتایج","section-title"))
        grid=Gtk.Grid(column_spacing=12,row_spacing=6)
        for cidx,t in enumerate(["روش","Ping","Download","Upload","وضعیت"]):grid.attach(label(t,"metric"),cidx,0,1,1)
        for ridx,key in enumerate(["AUTO","WARP","NODE","TOR","DIRECT"],start=1):
            grid.attach(label(key,xalign=1.0),0,ridx,1,1)
            vals=[]
            for cidx in range(1,5):
                v=label("—","muted");grid.attach(v,cidx,ridx,1,1);vals.append(v)
            self.compare_metric[key]=vals
        cmp.append(grid);root.append(cmp)
        return scroll(root)

    def method_card(self,key,title,desc,cap,compact=False):
        c=vbox(7);c.add_css_class("card");c.set_hexpand(True)
        head=hbox(6);t=vbox(1);t.set_hexpand(True);t.append(label(title,"method-title"));t.append(label(desc,"muted"));head.append(t)
        sel=Gtk.CheckButton();sel.set_tooltip_text("انتخاب روش");sel.connect("toggled",lambda b,k=key:self.method_toggle(k,b));head.append(sel);c.append(head)
        met=label("Ping — · Down — · Up —","muted");c.append(met);self.method_metric[key]=met
        pill=label(cap,"muted",xalign=.5);pill.add_css_class("pill");c.append(pill)
        if not compact:
            ar=hbox(6)
            connect=button("▶ اتصال",lambda *_k,k=key:self.connect_method(k),"primary")
            test=button("◔ تست",lambda *_k,k=key:self.test_method(k,False))
            ar.append(connect);ar.append(test);c.append(ar)
        self.method_cards[key]=(c,sel)
        return c

    def build_methods(self):
        root=vbox(12);root.set_margin_bottom(12);root.append(self.page_head("روش‌ها","انتخاب، تست قبل از اتصال و مقایسهٔ providerها"))
        scope=card();scope.append(label("Scope فعال","section-title"))
        r=hbox(8);r.set_homogeneous(True)
        for key,text in [("BROWSER","◎ مرورگر"),("SYSTEM","▣ کل سیستم"),("CONSOLE",">_ کنسول")]:
            b=button(text,lambda _b,k=key:self.set_scope(k));r.append(b)
        scope.append(r);root.append(scope)
        grid=Gtk.Grid(column_spacing=10,row_spacing=10)
        for i,(key,title,desc,cap) in enumerate(METHODS):
            grid.attach(self.method_card(key,title,desc,cap),i%2,i//2,1,1)
        root.append(grid)
        return scroll(root)

    def build_nodes(self):
        root=vbox(10);root.set_margin_bottom(12);root.append(self.page_head("Node Pool","VLESS / VMess / Shadowsocks / Trojan / Hysteria2"))

        ctl=card()
        row=hbox(7)
        row.append(button("⇩ دریافت نودهای عمومی",lambda *_:self.run_async("Node Refresh",core.node_refresh_public,self.nodes_done),"primary"))
        row.append(button("↻ تازه‌سازی لیست",lambda *_:self.refresh_nodes()))
        row.append(button("تست سریع همه",lambda *_:self.run_async("Node Test All",core.node_test_all,self.nodes_done)))
        row.append(button("Benchmark 4 نود",lambda *_:self.run_async("Node Benchmark Batch",lambda:core.node_benchmark_batch(4),self.nodes_done)))
        row.append(button("Ping + Speed منتخب",lambda *_:self.test_method("NODE",False)))
        ctl.append(row)

        imp=hbox(7)
        self.node_url=Gtk.Entry();self.node_url.set_placeholder_text("HTTPS subscription URL");self.node_url.set_hexpand(True);self.node_url.set_direction(Gtk.TextDirection.LTR)
        imp.append(self.node_url);imp.append(button("افزودن URL",self.import_node_url));imp.append(button("Import File",self.import_node_file));imp.append(button("Clipboard",self.import_node_clipboard));ctl.append(imp)
        ex=hbox(7);ex.append(button("Export Raw",lambda *_:self.export_nodes(False)));ex.append(button("Export Base64",lambda *_:self.export_nodes(True)));ctl.append(ex)

        filt=hbox(7);self.node_filter=Gtk.Entry();self.node_filter.set_placeholder_text("فیلتر نام / کشور / protocol / source");self.node_filter.set_hexpand(True);self.node_filter.connect("changed",lambda *_:self.refresh_nodes())
        self.node_sort=Gtk.DropDown.new_from_strings(["Smart","Ping","Download","Protocol","Name"]);self.node_sort.connect("notify::selected",lambda *_:self.refresh_nodes())
        filt.append(self.node_filter);filt.append(self.node_sort);ctl.append(filt)
        self.node_summary=label("لیست نودها هنوز خوانده نشده.","muted");ctl.append(self.node_summary)
        root.append(ctl)

        body=hbox(10)
        listcard=card();listcard.set_hexpand(True)
        self.node_list=Gtk.ListBox();self.node_list.set_selection_mode(Gtk.SelectionMode.SINGLE);self.node_list.connect("row-selected",self.node_row_selected)
        ns=Gtk.ScrolledWindow();ns.set_vexpand(True);ns.set_min_content_height(360);ns.set_child(self.node_list);listcard.append(ns);body.append(listcard)

        detail=card();detail.set_size_request(330,-1);detail.append(label("نود انتخاب‌شده","section-title"))
        self.node_detail=label("یک نود را انتخاب کن.","muted");detail.append(self.node_detail)
        nr=hbox(6);nr.append(button("انتخاب",self.select_current_node));nr.append(button("▶ اتصال",lambda *_:self.connect_method("NODE"),"primary"));detail.append(nr)
        nr2=hbox(6);nr2.append(button("⌁ Ping",lambda *_:self.test_method("NODE",True)));nr2.append(button("Ping + Speed",lambda *_:self.test_method("NODE",False)));detail.append(nr2)
        nr3=hbox(6);nr3.append(button("★ Favorite",lambda *_:self.toggle_node_meta("favorite")));nr3.append(button("📌 Pin",lambda *_:self.toggle_node_meta("pinned")));nr3.append(button("History",self.show_node_history));nr3.append(button("Copy Raw",self.copy_node_raw));detail.append(nr3)
        detail.append(label("Metadata","metric"))
        self.node_name_entry=Gtk.Entry();self.node_name_entry.set_placeholder_text("نام نمایشی");detail.append(self.node_name_entry)
        mr=hbox(6);mr.append(label("Rating 0–5","muted"));self.node_rating=Gtk.SpinButton.new_with_range(0,5,1);mr.append(self.node_rating);detail.append(mr)
        self.node_tags_entry=Gtk.Entry();self.node_tags_entry.set_placeholder_text("tags, comma, separated");detail.append(self.node_tags_entry)
        self.node_note_entry=Gtk.Entry();self.node_note_entry.set_placeholder_text("یادداشت");detail.append(self.node_note_entry)
        detail.append(button("ذخیره Metadata",self.save_node_metadata))
        detail.append(button("قطع Node",lambda *_:self.run_async("Node Stop",core.node_stop,self.nodes_done),"danger"))
        self.singbox_state=label("sing-box: در حال بررسی","muted");detail.append(self.singbox_state)
        body.append(detail);root.append(body)
        return root

    def build_tools(self):
        root=vbox(12);root.set_margin_bottom(12);root.append(self.page_head("ابزارها","Update / Diagnostics / Console / Bridges"))

        up=card();up.append(label("آپدیت و مسیر پایه","section-title"));up.append(label("بررسی update و دریافت نود، عملیات مستقل‌اند. هیچ VPN با باز شدن صفحه تغییر نمی‌کند.","muted"))
        rr=hbox(7);rr.append(button("↻ بررسی آپدیت GitHub",lambda *_:self.run_async("Update Check",core.update_check,self.update_done)));self.update_install_btn=button("⇧ نصب آپدیت",self.confirm_update_install,"primary");self.update_install_btn.set_sensitive(False);rr.append(self.update_install_btn);rr.append(button("⇩ دریافت نودهای جدید",lambda *_:self.run_async("Node Refresh",core.node_refresh_public,self.nodes_done),"primary"));up.append(rr)
        self.update_label=label("هنوز بررسی نشده.","muted");up.append(self.update_label);root.append(up)

        diag=card();diag.append(label("Diagnostics","section-title"))
        r=hbox(7)
        for text,name,fn in [
            ("موجودی","Inventory",core.inventory),
            ("Doctor","Doctor",core.doctor),
            ("تست اینترنت پایه","Direct Speed",lambda:core.benchmark_direct(False)),
            ("گزارش","Export",core.export_report),
        ]:r.append(button(text,lambda _b,n=name,f=fn:self.run_async(n,f)))
        diag.append(r);root.append(diag)

        con=card();con.append(label("اتصال کنسول","section-title"));con.append(label("Hotspot مستقل؛ فقط با اقدام صریح روشن می‌شود. Physical game/country E2E هنوز gate خارجی است.","muted"))
        cr=hbox(7);cr.append(button("وضعیت",lambda *_:self.run_async("Console Status",core.console_status,self.console_done)));cr.append(button("آماده‌سازی",self.confirm_console_prepare));cr.append(button("▶ اتصال کنسول",self.confirm_console_start,"primary"));cr.append(button("توقف",lambda *_:self.run_async("Console Stop",core.console_stop,self.console_done),"danger"));con.append(cr)
        self.console_label=label("در حال بررسی…","muted");con.append(self.console_label);root.append(con)

        br=card();br.append(label("Tor / Bridges","section-title"))
        tr=hbox(7);tr.append(button("Tor Direct",lambda *_:self.run_async("Tor Direct",lambda:legacy.start_tor("direct"))));tr.append(button("Tor obfs4",lambda *_:self.run_async("Tor obfs4",lambda:legacy.start_tor("obfs4"))));tr.append(button("Tor Snowflake",lambda *_:self.run_async("Tor Snowflake",lambda:legacy.start_tor("snowflake"))));tr.append(button("توقف Tor",lambda *_:self.run_async("Tor Stop",legacy.stop_tor),"danger"));br.append(tr)
        ir=hbox(7);ir.append(button("Import obfs4",self.import_bridges));ir.append(button("Import Snowflake",self.import_snowflake));br.append(ir)
        self.bridge_label=label("—","muted");br.append(self.bridge_label);root.append(br)

        logs=card();logs.append(label("خروجی عملیات","section-title"))
        self.details=Gtk.TextView();self.details.set_editable(False);self.details.set_monospace(True);self.details.set_direction(Gtk.TextDirection.LTR);self.details.get_buffer().set_text("No operation has started.")
        ds=Gtk.ScrolledWindow();ds.set_min_content_height(230);ds.set_child(self.details);logs.append(ds)
        lr=hbox(7);lr.append(button("کپی نتیجه",self.copy_details));lr.append(button("پوشه شواهد",self.open_evidence));logs.append(lr);root.append(logs)
        return scroll(root)

    def build_settings(self):
        root=vbox(12);root.set_margin_bottom(12);root.append(self.page_head("تنظیمات","رفتار UI، تست و مسیر شخصی"))

        s=core.settings()
        ui=card();ui.append(label("ظاهر و حریم خصوصی","section-title"))
        r=hbox(8);r.append(label("تم"));self.theme_drop=Gtk.DropDown.new_from_strings(["Dark","Light"]);self.theme_drop.set_selected(0 if s["theme"]=="dark" else 1);r.append(self.theme_drop)
        r.append(label("نمایش IP"));self.show_ip_switch=Gtk.Switch();self.show_ip_switch.set_active(bool(s["showIp"]));r.append(self.show_ip_switch);ui.append(r);root.append(ui)

        test=card();test.append(label("تنظیمات تست","section-title"))
        p=hbox(8);p.append(label("مسیر تست"));self.test_path=Gtk.DropDown.new_from_strings(["BASE · اینترنت فعلی سیستم","SELECTED · مسیر انتخاب‌شده"]);self.test_path.set_selected(0 if s["testPathMode"]=="BASE" else 1);p.append(self.test_path);test.append(p)
        grid=Gtk.Grid(column_spacing=8,row_spacing=8)
        self.ping_spin=Gtk.SpinButton.new_with_range(3,30,1);self.ping_spin.set_value(s["pingTimeoutSec"])
        self.down_spin=Gtk.SpinButton.new_with_range(10,120,5);self.down_spin.set_value(s["downloadTimeoutSec"])
        self.up_spin=Gtk.SpinButton.new_with_range(10,120,5);self.up_spin.set_value(s["uploadTimeoutSec"])
        for row,(txt,w) in enumerate([("Ping timeout",self.ping_spin),("Download timeout",self.down_spin),("Upload timeout",self.up_spin)]):
            grid.attach(label(txt),0,row,1,1);grid.attach(w,1,row,1,1)
        test.append(grid);root.append(test)

        conn=card();conn.append(label("کشور / Home / Custom Proxy","section-title"))
        country=hbox(8);country.append(label("کشور"));self.country_drop=Gtk.DropDown.new_from_strings(list(core.ALLOWED_COUNTRIES));self.country_drop.set_selected(list(core.ALLOWED_COUNTRIES).index(s["country"]));country.append(self.country_drop);conn.append(country)
        self.home_entry=Gtk.Entry();self.home_entry.set_text(str(s["home"]));self.home_entry.set_direction(Gtk.TextDirection.LTR);self.home_entry.set_placeholder_text("https://...")
        self.proxy_entry=Gtk.Entry();self.proxy_entry.set_text(str(s["customProxy"]));self.proxy_entry.set_direction(Gtk.TextDirection.LTR);self.proxy_entry.set_placeholder_text("socks5h://host:port or http://host:port")
        conn.append(label("Home URL","muted"));conn.append(self.home_entry);conn.append(label("Custom Proxy","muted"));conn.append(self.proxy_entry);root.append(conn)

        mon=card();mon.append(label("پایایی","section-title"))
        mr=hbox(8);mr.append(label("بررسی دوره‌ای"));self.monitor_switch=Gtk.Switch();self.monitor_switch.set_active(bool(s["monitor"]));mr.append(self.monitor_switch);mr.append(label("Auto-repair محدود Tor"));self.repair_switch=Gtk.Switch();self.repair_switch.set_active(bool(s["autoRepair"]));mr.append(self.repair_switch);mon.append(mr);root.append(mon)
        root.append(button("ذخیره تنظیمات",self.save_settings,"primary"))
        return scroll(root)

    def show_page(self,name):
        if self.stack:self.stack.set_visible_child_name(name)
        for k,b in self.nav.items():
            if k==name:b.add_css_class("suggested-action")
            else:b.remove_css_class("suggested-action")
        if name=="nodes":self.refresh_nodes()

    def set_scope(self,scope,widget=None):
        self.scope=scope
        names={"BROWSER":"مرورگر","SYSTEM":"کل سیستم","CONSOLE":"کنسول"}
        self.sidebar_scope.set_text("Scope: "+names.get(scope,scope))
        for k in ("BROWSER","SYSTEM","CONSOLE"):
            b=getattr(self,"scope_"+k.lower(),None)
            if b and b.get_active()!=(k==scope):
                b.set_active(k==scope)
        if scope=="CONSOLE":self.status_detail.set_text("Console Gateway مستقل انتخاب شد.")
        elif scope=="SYSTEM":self.status_detail.set_text("Full System در Linux برای WARP رسمی پذیرفته شده است.")
        else:self.status_detail.set_text("Browser scope پیش‌فرض امن است.")
        return False

    def method_toggle(self,key,b):
        if not b.get_active():return
        self.select_method(key)

    def select_method(self,key):
        self.method=key
        for k,(c,b) in self.method_cards.items():
            if b.get_active()!=(k==key):b.set_active(k==key)
            if k==key:c.add_css_class("card-selected")
            else:c.remove_css_class("card-selected")
        title=next((x[1] for x in METHODS if x[0]==key),key);self.sidebar_method.set_text("Method: "+title)

    def connect_selected(self):
        self.connect_method(self.method)

    def connect_method(self,method):
        if self.scope=="CONSOLE":
            self.confirm_console_start();return
        self.select_method(method)
        self.run_async(f"Connect {self.scope} {method}",lambda:core.connect_method(method,self.scope),self.connect_done)

    def connect_done(self,result):
        if result.get("guard",{}).get("token"):
            self.pending_warp_token=result["guard"]["token"];self.keep_btn.set_sensitive(True)
        self.refresh_all()

    def keep_warp(self,*_):
        if not self.pending_warp_token:return
        token=self.pending_warp_token
        def done(r):
            if r.get("ok"):self.pending_warp_token=None;self.keep_btn.set_sensitive(False)
        self.run_async("Keep WARP",lambda:legacy.warp_keep(token),done)

    def test_selected(self,ping_only):
        self.select_method(self.method)
        self.run_async(
            ("Ping " if ping_only else "Benchmark ")+self.method+" · "+str(core.settings().get("testPathMode") or "BASE"),
            lambda:core.benchmark_configured(self.method,ping_only),
            lambda r,m=self.method:self.metric_done(m,r),
        )

    def test_method(self,method,ping_only=False):
        self.select_method(method)
        self.run_async(("Ping " if ping_only else "Benchmark ")+method,lambda:core.benchmark_method(method,ping_only),lambda r,m=method:self.metric_done(m,r))

    def metric_done(self,method,result):
        self.metrics[method]=result
        p=result.get("pingMs");d=result.get("downloadMbps");u=result.get("uploadMbps")
        fmt=f"Ping {p if p is not None else '—'} · Down {d if d is not None else '—'} · Up {u if u is not None else '—'}"
        if method in self.method_metric:self.method_metric[method].set_text(fmt)
        key="AUTO" if method.startswith("AUTO") else method
        if key in self.compare_metric:
            vals=self.compare_metric[key];vals[0].set_text("—" if p is None else f"{p} ms");vals[1].set_text("—" if d is None else f"{d} Mbps");vals[2].set_text("—" if u is None else f"{u} Mbps");vals[3].set_text("PASS" if result.get("ok") else str(result.get("error") or "FAIL"))
        self.dash_ping.set_text("—" if p is None else f"{p} ms")
        self.refresh_nodes()

    def set_busy(self,value,text=None):
        self.busy=value
        if text:self.sidebar_state.set_text(text)

    def run_async(self,name,fn,on_done=None):
        if self.busy:return
        self.set_busy(True,"در حال اجرا: "+name)
        if hasattr(self,"status_detail"):self.status_detail.set_text("در حال انجام "+name+"…")
        def worker():
            try:r=fn()
            except Exception as e:r={"ok":False,"error":type(e).__name__+": "+str(e)}
            GLib.idle_add(self.finish_action,name,r,on_done)
        threading.Thread(target=worker,daemon=True).start()

    def finish_action(self,name,result,on_done):
        self.set_busy(False)
        if hasattr(self,"details"):self.details.get_buffer().set_text(json.dumps(result,ensure_ascii=False,indent=2))
        ok=bool(result and result.get("ok"))
        self.sidebar_state.set_text("موفق" if ok else "نیاز به توجه");self.sidebar_detail.set_text(name)
        if result and result.get("error"):
            self.status_title.set_text("عملیات کامل نشد");self.status_detail.set_text(str(result.get("error")))
        if on_done:on_done(result or {})
        self.refresh_snapshot()
        return False

    def refresh_all(self):
        self.refresh_snapshot();self.refresh_nodes();self.refresh_aux()

    def refresh_snapshot(self):
        try:s=core.current_snapshot()
        except Exception as e:s={"ok":False,"error":str(e)}
        mode=s.get("mode") or "—";provider=s.get("provider") or "—";country=s.get("country") or "—";warp=s.get("warp") or ""
        if not warp and isinstance(s.get("trace"),dict):warp=(s.get("trace") or {}).get("trace",{}).get("warp","")
        self.dash_route.set_text(str(provider));self.dash_country.set_text("Tor / نامشخص" if country=="T1" else str(country));self.dash_warp.set_text(str(warp or "off"))
        ip=s.get("ip") or (s.get("trace") or {}).get("trace",{}).get("ip","") if isinstance(s.get("trace"),dict) else s.get("ip","")
        self.dash_ip.set_text(str(ip or "—") if core.settings().get("showIp") else "پنهان")
        if s.get("ok") and s.get("mode"):
            self.status_title.set_text("مسیر تأیید شد");self.status_detail.set_text(f"{mode} · {provider} · {s.get('scope','—')}");self.sidebar_state.set_text("متصل")
        elif not s.get("mode"):
            self.status_title.set_text("آمادهٔ انتخاب مسیر");self.status_detail.set_text("باز شدن برنامه هیچ VPN یا proxy را روشن نمی‌کند.");self.sidebar_state.set_text("آماده")
        else:
            self.status_title.set_text("مسیر نیاز به بررسی دارد");self.status_detail.set_text(str(s.get("error") or "—"))

    def refresh_aux(self):
        st=core.singbox_status();self.singbox_state.set_text("sing-box: "+(("آماده" if st.get("ok") else str(st.get("error") or "ناموجود"))))
        self.bridge_label.set_text(f"obfs4: {len(legacy.bridge_lines(legacy.BRIDGES))} · Snowflake: {len(legacy.bridge_lines(legacy.SNOWFLAKE_BRIDGES))}")
        try:self.console_done(core.console_status())
        except Exception:pass

    def refresh_nodes(self):
        rows=core.node_rows();flt=(self.node_filter.get_text().strip().lower() if hasattr(self,"node_filter") else "")
        if flt:
            rows=[n for n in rows if flt in " ".join(str(n.get(k) or "") for k in ("name","protocol","source","server","tags")).lower()]
        idx=self.node_sort.get_selected() if hasattr(self,"node_sort") else 0
        def key(n):
            ep=n.get("endpoint_test") or {};perf=n.get("performance_test") or {}
            if idx==1:return float(ep.get("latency_ms") or 999999)
            if idx==2:return -float(perf.get("downloadMbps") or 0)
            if idx==3:return str(n.get("protocol") or "")
            if idx==4:return str(n.get("name") or "").lower()
            return (0 if n.get("pinned") else 1,0 if n.get("favorite") else 1,0 if ep.get("reachable") else 1,float(ep.get("latency_ms") or 999999))
        rows=sorted(rows,key=key);self.node_cache=rows
        if hasattr(self,"node_list"):
            while True:
                child=self.node_list.get_first_child()
                if child is None:break
                self.node_list.remove(child)
            selected=core.node_store().get("selected")
            for n in rows[:500]:
                row=Gtk.ListBoxRow();row.node_id=n.get("id")
                box=hbox(8);box.add_css_class("node-row")
                name=vbox(1);name.set_hexpand(True);name.append(label(("📌 " if n.get("pinned") else "")+("★ " if n.get("favorite") else "")+str(n.get("name") or "Node"),"metric"));name.append(label(f"{n.get('protocol')} · {n.get('server')}:{n.get('port')} · {n.get('source')}","muted"));box.append(name)
                ep=n.get("endpoint_test") or {};perf=n.get("performance_test") or {};lat=ep.get("latency_ms")
                box.append(label("—" if lat is None else f"{lat} ms","muted",xalign=.5));box.append(label("—" if perf.get("downloadMbps") is None else f"{perf.get('downloadMbps')} Mbps","muted",xalign=.5))
                if n.get("id")==selected:box.add_css_class("card-selected")
                row.set_child(box);self.node_list.append(row)
            self.node_summary.set_text(f"{len(rows)} نود نمایش داده می‌شود · کل {len(core.node_store()['nodes'])} · selected={selected[:8] if selected else '—'}")
        return False

    def node_row_selected(self,_list,row):
        if not row:return
        self.selected_node_id=getattr(row,"node_id","")
        n=next((x for x in self.node_cache if x.get("id")==self.selected_node_id),None)
        if not n:return
        ep=n.get("endpoint_test") or {};perf=n.get("performance_test") or {}
        self.node_detail.set_text(f"{n.get('name')}\n{n.get('protocol')} · {n.get('server')}:{n.get('port')}\nPing: {ep.get('latency_ms','—')} ms · Down: {perf.get('downloadMbps','—')} · Up: {perf.get('uploadMbps','—')}\nSource: {n.get('source')}")
        self.node_name_entry.set_text(str(n.get("name") or ""))
        self.node_rating.set_value(float(n.get("rating") or 0))
        self.node_tags_entry.set_text(", ".join(str(x) for x in (n.get("tags") or [])))
        self.node_note_entry.set_text(str(n.get("note") or ""))

    def select_current_node(self,*_):
        if not self.selected_node_id:return
        try:core.node_select(self.selected_node_id);self.refresh_nodes()
        except Exception as e:self.status_detail.set_text(str(e))

    def toggle_node_meta(self,key):
        if not self.selected_node_id:return
        n=next((x for x in self.node_cache if x.get("id")==self.selected_node_id),None)
        if not n:return
        core.node_update_meta(self.selected_node_id,{key:not bool(n.get(key))});self.refresh_nodes()

    def save_node_metadata(self,*_):
        if not self.selected_node_id:return
        tags=[x.strip() for x in self.node_tags_entry.get_text().split(",") if x.strip()]
        patch={"name":self.node_name_entry.get_text().strip(),"rating":int(self.node_rating.get_value()),"tags":tags,"note":self.node_note_entry.get_text()}
        try:core.node_update_meta(self.selected_node_id,patch);self.refresh_nodes();self.status_detail.set_text("Metadata نود ذخیره شد.")
        except Exception as e:self.status_detail.set_text(str(e))

    def show_node_history(self,*_):
        if not self.selected_node_id:return
        try:r=core.node_history(self.selected_node_id)
        except Exception as e:r={"ok":False,"error":str(e)}
        self.details.get_buffer().set_text(json.dumps(r,ensure_ascii=False,indent=2));self.show_page("tools")

    def copy_node_raw(self,*_):
        if not self.selected_node_id:return
        try:raw=core.node_raw(self.selected_node_id)
        except Exception as e:self.status_detail.set_text(str(e));return
        Gdk.Display.get_default().get_clipboard().set(raw);self.status_detail.set_text("Raw node در clipboard کپی شد.")

    def export_nodes(self,base64_mode=False):
        chooser=Gtk.FileChooserNative.new("Export Nodes",self.win,Gtk.FileChooserAction.SAVE,"ذخیره","لغو")
        chooser.set_current_name("FreeNetHub_nodes.b64.txt" if base64_mode else "FreeNetHub_nodes.txt")
        def resp(d,r):
            if r==Gtk.ResponseType.ACCEPT and d.get_file():
                p=d.get_file().get_path();self.run_async("Node Export",lambda:core.node_export(p,base64_mode))
            d.destroy()
        chooser.connect("response",resp);chooser.show()

    def nodes_done(self,result):
        self.refresh_nodes();self.refresh_aux()

    def import_node_url(self,*_):
        url=self.node_url.get_text().strip()
        if url:self.run_async("Node Import URL",lambda:core.node_import_url(url),self.nodes_done)

    def import_node_clipboard(self,*_):
        clip=Gdk.Display.get_default().get_clipboard()
        def got(_clip,res):
            try:text=clip.read_text_finish(res)
            except Exception as e:self.status_detail.set_text(str(e));return
            if text:self.run_async("Node Import Clipboard",lambda:core.node_import_text(text,"clipboard"),self.nodes_done)
        clip.read_text_async(None,got)

    def import_node_file(self,*_):
        chooser=Gtk.FileChooserNative.new("Import Node File",self.win,Gtk.FileChooserAction.OPEN,"انتخاب","لغو")
        def resp(d,r):
            if r==Gtk.ResponseType.ACCEPT and d.get_file():
                p=d.get_file().get_path();self.run_async("Node Import File",lambda:core.node_import_file(p),self.nodes_done)
            d.destroy()
        chooser.connect("response",resp);chooser.show()

    def update_done(self,result):
        if result.get("ok"):
            a=result.get("linuxAsset");available=bool(result.get("updateAvailable"))
            self.update_label.set_text(f"Current R{result.get('localRevision','—')} · Remote R{result.get('remoteRevision','—')} · {result.get('tag')} · "+("آپدیت جدید موجود است" if available else "به‌روز"))
            self.update_install_btn.set_sensitive(available)
        else:
            self.update_label.set_text(str(result.get("error") or "خطا"));self.update_install_btn.set_sensitive(False)

    def confirm_update_install(self,*_):
        self.confirm("نصب آپدیت Linux","فقط اگر revision جدیدتر و SHA-256 معتبر باشد دانلود و نصب می‌شود. Installer فقط UI FreeNet Hub را restart می‌کند و اتصال شبکه را روشن نمی‌کند.",lambda:self.run_async("Install Update",core.update_install))

    def console_done(self,result):
        if not hasattr(self,"console_label"):return
        if result.get("state")=="hotspot-up":self.console_label.set_text("Console Hotspot روشن است.")
        elif result.get("config"):self.console_label.set_text("Console آماده است؛ physical validation جداست.")
        elif result.get("error"):self.console_label.set_text("خطا: "+str(result.get("error")))
        else:self.console_label.set_text("Console خاموش / آماده بررسی")

    def confirm_console_prepare(self,*_):
        self.confirm("آماده‌سازی Console","NetworkManager profile محلی ساخته/به‌روزرسانی می‌شود؛ هنوز روشن نمی‌شود.",lambda:self.run_async("Console Prepare",core.console_prepare,self.console_done))

    def confirm_console_start(self,*_,**__):
        self.confirm("اتصال Console","Hotspot کنسول روشن می‌شود. تغییر فقط با اقدام صریح شما انجام می‌شود.",lambda:self.run_async("Console Start",core.console_start,self.console_done))

    def confirm(self,title,text,yes):
        d=Gtk.MessageDialog(transient_for=self.win,modal=True,buttons=Gtk.ButtonsType.YES_NO,message_type=Gtk.MessageType.QUESTION,text=title,secondary_text=text)
        def resp(x,r):
            x.destroy()
            if r==Gtk.ResponseType.YES:yes()
        d.connect("response",resp);d.present()

    def save_settings(self,*_):
        patch={
            "theme":"dark" if self.theme_drop.get_selected()==0 else "light",
            "showIp":self.show_ip_switch.get_active(),
            "testPathMode":"BASE" if self.test_path.get_selected()==0 else "SELECTED",
            "pingTimeoutSec":int(self.ping_spin.get_value()),
            "downloadTimeoutSec":int(self.down_spin.get_value()),
            "uploadTimeoutSec":int(self.up_spin.get_value()),
            "country":core.ALLOWED_COUNTRIES[self.country_drop.get_selected()],
            "home":self.home_entry.get_text().strip(),
            "customProxy":self.proxy_entry.get_text().strip(),
            "monitor":self.monitor_switch.get_active(),
            "autoRepair":self.repair_switch.get_active(),
        }
        def done(r):
            if r.get("ok"):self.apply_theme(r["settings"]["theme"]=="dark")
        self.run_async("Save Settings",lambda:core.save_settings(patch),done)

    def import_bridges(self,*_):
        chooser=Gtk.FileChooserNative.new("انتخاب فایل obfs4",self.win,Gtk.FileChooserAction.OPEN,"انتخاب","لغو")
        def resp(d,r):
            if r==Gtk.ResponseType.ACCEPT and d.get_file():p=d.get_file().get_path();self.run_async("Import obfs4",lambda:core.import_obfs4(p),lambda _r:self.refresh_aux())
            d.destroy()
        chooser.connect("response",resp);chooser.show()

    def import_snowflake(self,*_):
        chooser=Gtk.FileChooserNative.new("انتخاب فایل Snowflake",self.win,Gtk.FileChooserAction.OPEN,"انتخاب","لغو")
        def resp(d,r):
            if r==Gtk.ResponseType.ACCEPT and d.get_file():p=d.get_file().get_path();self.run_async("Import Snowflake",lambda:core.import_snowflake(p),lambda _r:self.refresh_aux())
            d.destroy()
        chooser.connect("response",resp);chooser.show()

    def copy_details(self,*_):
        b=self.details.get_buffer();txt=b.get_text(b.get_start_iter(),b.get_end_iter(),True);Gdk.Display.get_default().get_clipboard().set(txt)

    def open_evidence(self,*_):
        legacy.ensure_dirs();subprocess.Popen(["xdg-open",str(legacy.EVIDENCE)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

    def periodic_refresh(self):
        if not self.busy:self.refresh_snapshot()
        s=core.settings()
        if s.get("monitor") and not self.busy:
            def worker():
                try:r=core.current_snapshot()
                except Exception as e:r={"ok":False,"error":str(e)}
                GLib.idle_add(self.monitor_done,r)
            threading.Thread(target=worker,daemon=True).start()
        return True

    def monitor_done(self,r):
        if r.get("ok"):self.monitor_failures=0
        else:self.monitor_failures+=1
        if self.monitor_failures>=3 and core.settings().get("autoRepair") and legacy.session().get("mode")=="TOR" and self.repairs<2:
            self.repairs+=1;self.monitor_failures=0;self.run_async("Tor Auto Repair",legacy.start_tor)
        return False

if __name__=="__main__":
    legacy.ensure_dirs()
    raise SystemExit(FreeNetHub().run(sys.argv))
