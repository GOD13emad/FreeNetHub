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

def flow(widgets=None,max_children=4,min_children=1,homogeneous=True,spacing=7):
    f=Gtk.FlowBox()
    f.set_selection_mode(Gtk.SelectionMode.NONE)
    f.set_homogeneous(homogeneous)
    f.set_min_children_per_line(min_children)
    f.set_max_children_per_line(max_children)
    f.set_column_spacing(spacing);f.set_row_spacing(spacing)
    for w in widgets or []:f.append(w)
    return f

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
        self.scope_buttons={}
        self.all_test_results={}
        self.node_sort_idx=0
        self.node_sort_buttons=[]
        self._syncing_sort=False
        self.monitor_failures=0
        self.repairs=0
        self._syncing_ip=False

    def do_activate(self):
        if self.win:
            self.win.present();return
        Gtk.Widget.set_default_direction(Gtk.TextDirection.RTL)
        self.apply_theme(self.dark)

        self.win=Adw.ApplicationWindow(application=self)
        self.win.set_title(f"FreeNet Hub · {core.VERSION}")
        self.win.set_default_size(1000,650)
        self.win.set_size_request(720,480)

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
        side=self.build_sidebar();side.set_size_request(205,-1);outer.append(side)

        self.stack=Gtk.Stack();self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE);self.stack.set_vexpand(True)
        self.stack.add_named(self.build_dashboard(),"dashboard")
        self.stack.add_named(self.build_methods(),"methods")
        self.stack.add_named(self.build_nodes(),"nodes")
        self.stack.add_named(self.build_tools(),"tools")
        self.stack.add_named(self.build_settings(),"settings")
        main.append(self.stack)

        toolbar=Adw.ToolbarView();toolbar.add_top_bar(hb);toolbar.set_content(outer)
        self.win.set_content(toolbar)
        self.select_method(self.method)
        self.set_scope(self.scope)
        self.show_page("dashboard")
        self.win.present()
        self.refresh_all()
        GLib.timeout_add_seconds(2,self.auto_update_check_once)
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
        f=label("Explicit connect · Fail-closed\nNo terminal window · No auto VPN","muted");f.set_valign(Gtk.Align.END);b.append(f)
        sc=Gtk.ScrolledWindow();sc.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);sc.set_propagate_natural_height(False);sc.set_child(b)
        return sc

    def page_head(self,title,subtitle):
        h=vbox(2);h.append(label(title,"title-big"));h.append(label(subtitle,"muted"));return h

    def build_dashboard(self):
        root=vbox(12);root.set_margin_bottom(12);root.append(self.page_head("داشبورد","۱) Scope را انتخاب کن  ۲) روش را انتخاب کن  ۳) تست کن  ۴) اتصال را بزن"))

        status=card()
        top=hbox(10);st=vbox(2);st.set_hexpand(True)
        self.status_title=label("در حال خواندن وضعیت","section-title");self.status_detail=label("—","muted")
        st.append(self.status_title);st.append(self.status_detail);top.append(st)
        top.append(button("باز کردن مرورگر",lambda *_:self.run_async("Browser",core.open_browser)))
        status.append(top)

        metrics=flow(max_children=4,min_children=2,spacing=8)
        for title,attr in [("مسیر","dash_route"),("کشور","dash_country"),("WARP","dash_warp"),("Ping","dash_ping")]:
            m=vbox(2);m.add_css_class("soft");m.append(label(title,"muted"));v=label("—","metric");setattr(self,attr,v);m.append(v);metrics.append(m)
        status.append(metrics)

        iprow=hbox(8);iprow.add_css_class("soft")
        iprow.append(label("IP عمومی","muted"));self.dash_ip=label("پنهان","metric",xalign=0.0);self.dash_ip.set_selectable(True);self.dash_ip.set_hexpand(True);iprow.append(self.dash_ip)
        iprow.append(label("نمایش IP","muted"));self.dashboard_ip_switch=Gtk.Switch();self.dashboard_ip_switch.set_active(bool(core.settings().get("showIp")));self.dashboard_ip_switch.connect("notify::active",self.dashboard_ip_changed);iprow.append(self.dashboard_ip_switch)
        status.append(iprow)
        root.append(status)

        scopes=card();scopes.append(label("۱ · محدوده اتصال (Scope)","section-title"));scopes.append(label("مرورگر امن‌ترین حالت پیش‌فرض است. «کل سیستم» در Linux R11 فقط WARP رسمی است.","muted"))
        scope_widgets=[]
        for key,text,sub in [
            ("BROWSER","◎ مرورگر","فقط مرورگر/پروفایل FreeNet Hub"),
            ("SYSTEM","▣ کل سیستم","WARP رسمی برای کل سیستم"),
            ("CONSOLE",">_ کنسول","Hotspot/Gateway مستقل کنسول"),
        ]:
            b=Gtk.ToggleButton();inner=vbox(2);inner.append(label(text,"metric",xalign=.5));inner.append(label(sub,"muted",xalign=.5));b.set_child(inner);b.add_css_class("scope");b.connect("toggled",lambda x,k=key:self.scope_toggled(k,x));scope_widgets.append(b);self.scope_buttons.setdefault(key,[]).append(b)
        scopes.append(flow(scope_widgets,max_children=3,min_children=1,spacing=8));root.append(scopes)

        choose=card()
        ch=hbox(8);txt=vbox(2);txt.set_hexpand(True);txt.append(label("۲ · روش اتصال","section-title"));self.selected_method_label=label("روش انتخاب‌شده: هوشمند","good");txt.append(self.selected_method_label);txt.append(label("روی «انتخاب» هر کارت بزن؛ کارت انتخاب‌شده با کادر مشخص می‌شود.","muted"));ch.append(txt)
        ch.append(button("نمایش همه روش‌ها",lambda *_:self.show_page("methods")));choose.append(ch)
        quick=[]
        for key in ["AUTO","NODE","WARP","TOR","DIRECT"]:
            title,desc,cap=next((x[1],x[2],x[3]) for x in METHODS if x[0]==key)
            quick.append(self.method_card(key,title,desc,cap,compact=True))
        choose.append(flow(quick,max_children=3,min_children=1,spacing=8));root.append(choose)

        act=card();act.append(label("۳ · تست و ۴ · اتصال","section-title"))
        act.append(label("«اینترنت اصلی» بدون ورود به provider تست می‌شود. «روش انتخاب‌شده» همان Node/WARP/Tor/... را واقعاً تست می‌کند.","muted"))
        actions=[
            button("تست اینترنت اصلی · Ping + Speed",lambda *_:self.test_base(False)),
            button("Ping روش انتخاب‌شده",lambda *_:self.test_selected(True)),
            button("تست کامل روش انتخاب‌شده",lambda *_:self.test_selected(False),"primary"),
            button("تست سریع همه روش‌ها",lambda *_:self.test_all_methods(True)),
            button("تست کامل همه روش‌ها",lambda *_:self.test_all_methods(False)),
            button("▶ اتصال روش انتخاب‌شده",lambda *_:self.connect_selected(),"primary"),
        ]
        self.keep_btn=button("نگه‌داشتن WARP",self.keep_warp);self.keep_btn.set_sensitive(False);actions.append(self.keep_btn)
        act.append(flow(actions,max_children=3,min_children=1,spacing=8));root.append(act)

        cmp=card();cmp.append(label("نتیجه آخرین تست روش‌ها","section-title"))
        grid=Gtk.Grid(column_spacing=12,row_spacing=6)
        for cidx,t in enumerate(["روش","Ping","Download","Upload","وضعیت"]):grid.attach(label(t,"metric"),cidx,0,1,1)
        for ridx,key in enumerate(["AUTO","NODE","WARP","GOOL","CFON","TOR","CUSTOM","DIRECT"],start=1):
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
        sel=Gtk.ToggleButton(label="انتخاب");sel.set_tooltip_text("این روش را برای تست/اتصال انتخاب کن");sel.connect("toggled",lambda b,k=key:self.method_toggle(k,b));head.append(sel);c.append(head)
        met=label("Ping — · Down — · Up —","muted");c.append(met);self.method_metric.setdefault(key,[]).append(met)
        pill=label(cap,"muted",xalign=.5);pill.add_css_class("pill");c.append(pill)
        if not compact:
            ar=[
                button("▶ اتصال",lambda *_k,k=key:self.connect_method(k),"primary"),
                button("Ping",lambda *_k,k=key:self.test_method(k,True)),
                button("Ping + Speed",lambda *_k,k=key:self.test_method(k,False)),
            ]
            c.append(flow(ar,max_children=3,min_children=1,spacing=6))
        self.method_cards.setdefault(key,[]).append((c,sel))
        return c

    def build_methods(self):
        root=vbox(12);root.set_margin_bottom(12);root.append(self.page_head("روش‌ها","هر کارت: انتخاب، Ping، تست کامل و اتصال"))

        current=card();current.append(label("روش و Scope فعال","section-title"));self.methods_current=label("هوشمند · مرورگر","good");current.append(self.methods_current)
        sw=[]
        for key,text in [("BROWSER","◎ مرورگر"),("SYSTEM","▣ کل سیستم"),("CONSOLE",">_ کنسول")]:
            b=Gtk.ToggleButton(label=text);b.connect("toggled",lambda x,k=key:self.scope_toggled(k,x));sw.append(b);self.scope_buttons.setdefault(key,[]).append(b)
        current.append(flow(sw,max_children=3,min_children=1));root.append(current)

        alltests=card();alltests.append(label("تست همه روش‌ها","section-title"));alltests.append(label("تست‌ها به‌ترتیب اجرا می‌شوند تا port/providerها با هم تداخل نکنند. اگر اتصال FreeNet Hub فعال باشد، برای حفظ state تست همه متوقف می‌شود.","muted"))
        alltests.append(flow([
            button("تست سریع همه · Ping",lambda *_:self.test_all_methods(True)),
            button("تست کامل همه · Ping + Download + Upload",lambda *_:self.test_all_methods(False),"primary"),
            button("تست اینترنت اصلی",lambda *_:self.test_base(False)),
        ],max_children=3,min_children=1))
        root.append(alltests)

        cards=[]
        for key,title,desc,cap in METHODS:cards.append(self.method_card(key,title,desc,cap))
        root.append(flow(cards,max_children=2,min_children=1,spacing=10))
        return scroll(root)

    def build_nodes(self):
        root=vbox(10);root.set_margin_bottom(12);root.append(self.page_head("Node Pool","نودها را دریافت کن، تست اولیه بگیر، سپس نودهای برتر را با Ping/Speed واقعی بسنج"))

        guide=card();guide.append(label("روش کار نودها","section-title"))
        guide.append(label("۱) «تست اولیه همه» فقط دسترسی endpoint را سریع می‌سنجد.  ۲) «تست واقعی 4 نود برتر» از proxy واقعی Ping/Download/Upload می‌گیرد.  ۳) روی هر ردیف کلیک کنی همان نود برای اتصال/تست انتخاب می‌شود.","muted"))
        guide.append(flow([
            button("⇩ دریافت نودهای عمومی",lambda *_:self.run_async("Node Refresh",core.node_refresh_public,self.nodes_done),"primary"),
            button("۱ · تست اولیه همه نودها (TCP)",lambda *_:self.run_async("Node Test All",core.node_test_all,self.nodes_done)),
            button("۲ · تست واقعی 4 نود برتر",lambda *_:self.run_async("Node Benchmark Batch",lambda:core.node_benchmark_batch(4),self.nodes_done),"primary"),
            button("تست کامل نود منتخب",lambda *_:self.test_method("NODE",False)),
            button("↻ تازه‌سازی نمایش",lambda *_:self.refresh_nodes()),
        ],max_children=3,min_children=1))
        root.append(guide)

        imp=card();imp.append(label("افزودن / خروجی گرفتن نود","section-title"))
        self.node_url=Gtk.Entry();self.node_url.set_placeholder_text("HTTPS subscription URL");self.node_url.set_hexpand(True);self.node_url.set_direction(Gtk.TextDirection.LTR);imp.append(self.node_url)
        imp.append(flow([
            button("افزودن URL",self.import_node_url),
            button("Import File",self.import_node_file),
            button("Clipboard",self.import_node_clipboard),
            button("Export Raw",lambda *_:self.export_nodes(False)),
            button("Export Base64",lambda *_:self.export_nodes(True)),
        ],max_children=5,min_children=1))
        root.append(imp)

        filt=card();filt.append(label("فیلتر و مرتب‌سازی","section-title"))
        self.node_filter=Gtk.Entry();self.node_filter.set_placeholder_text("فیلتر: نام / کشور / پروتکل / منبع / سرور");self.node_filter.set_hexpand(True);self.node_filter.connect("changed",lambda *_:self.refresh_nodes());filt.append(self.node_filter)
        filt.append(label("مرتب‌سازی بر اساس:","muted"))
        self.node_sort_buttons=[]
        sort_widgets=[]
        sort_group=None
        for i,text in enumerate(["هوشمند","کمترین Ping","بیشترین Download","بیشترین Upload","کشور","پروتکل","نام"]):
            b=Gtk.ToggleButton(label=text)
            if sort_group is None:sort_group=b
            else:b.set_group(sort_group)
            b.connect("toggled",lambda x,idx=i:self.node_sort_toggled(idx,x))
            self.node_sort_buttons.append(b);sort_widgets.append(b)
        filt.append(flow(sort_widgets,max_children=4,min_children=2,spacing=6))
        self._syncing_sort=True
        self.node_sort_buttons[0].set_active(True)
        self._syncing_sort=False
        self.node_summary=label("لیست نودها هنوز خوانده نشده.","muted");filt.append(self.node_summary);root.append(filt)

        listcard=card();listcard.append(label("لیست نودها · روی ردیف کلیک کن تا انتخاب شود","section-title"))
        self.node_list=Gtk.ListBox();self.node_list.set_selection_mode(Gtk.SelectionMode.SINGLE);self.node_list.connect("row-selected",self.node_row_selected)
        ns=Gtk.ScrolledWindow();ns.set_vexpand(True);ns.set_min_content_height(320);ns.set_max_content_height(430);ns.set_propagate_natural_height(True);ns.set_child(self.node_list);listcard.append(ns);root.append(listcard)

        detail=card();detail.append(label("نود انتخاب‌شده","section-title"))
        self.node_detail=label("یک ردیف از لیست را انتخاب کن.","muted");detail.append(self.node_detail)
        detail.append(flow([
            button("✓ انتخاب این نود",self.select_current_node),
            button("▶ اتصال Node",lambda *_:self.connect_method("NODE"),"primary"),
            button("Ping نود منتخب",lambda *_:self.test_method("NODE",True)),
            button("Ping + Download + Upload",lambda *_:self.test_method("NODE",False)),
            button("★ Favorite",lambda *_:self.toggle_node_meta("favorite")),
            button("📌 Pin",lambda *_:self.toggle_node_meta("pinned")),
            button("History",self.show_node_history),
            button("Copy Raw",self.copy_node_raw),
            button("قطع Node",lambda *_:self.run_async("Node Stop",core.node_stop,self.nodes_done),"danger"),
        ],max_children=4,min_children=1))
        detail.append(label("Metadata","metric"))
        self.node_name_entry=Gtk.Entry();self.node_name_entry.set_placeholder_text("نام نمایشی");detail.append(self.node_name_entry)
        mr=hbox(6);mr.append(label("Rating 0–5","muted"));self.node_rating=Gtk.SpinButton.new_with_range(0,5,1);mr.append(self.node_rating);detail.append(mr)
        self.node_tags_entry=Gtk.Entry();self.node_tags_entry.set_placeholder_text("tags, comma, separated");detail.append(self.node_tags_entry)
        self.node_note_entry=Gtk.Entry();self.node_note_entry.set_placeholder_text("یادداشت");detail.append(self.node_note_entry)
        detail.append(button("ذخیره Metadata",self.save_node_metadata))
        self.singbox_state=label("sing-box: در حال بررسی","muted");detail.append(self.singbox_state);root.append(detail)
        return scroll(root)

    def build_tools(self):
        root=vbox(12);root.set_margin_bottom(12);root.append(self.page_head("ابزارها","Update / Diagnostics / Console / Bridges"))

        up=card();up.append(label("آپدیت مستقیم","section-title"));up.append(label("بررسی آپدیت خودکار و read-only است. نصب فقط با کلیک شما انجام می‌شود و asset باید SHA-256 معتبر GitHub داشته باشد.","muted"))
        self.update_install_btn=button("نصب آپدیت پیدا‌شده",self.confirm_update_install,"primary");self.update_install_btn.set_sensitive(False)
        up.append(flow([
            button("↻ فقط بررسی آپدیت",lambda *_:self.run_async("Update Check",core.update_check,self.update_done)),
            button("⬆ بررسی و نصب مستقیم آخرین نسخه",self.direct_update_clicked,"primary"),
            self.update_install_btn,
            button("⇩ دریافت نودهای جدید",lambda *_:self.run_async("Node Refresh",core.node_refresh_public,self.nodes_done)),
        ],max_children=4,min_children=1))
        self.update_label=label("در حال بررسی نسخه…","muted");up.append(self.update_label);root.append(up)

        diag=card();diag.append(label("Diagnostics و تست مسیر","section-title"))
        diag.append(flow([
            button("Inventory",lambda *_:self.run_async("Inventory",core.inventory)),
            button("Doctor",lambda *_:self.run_async("Doctor",core.doctor)),
            button("تست اینترنت اصلی",lambda *_:self.test_base(False)),
            button("گزارش",lambda *_:self.run_async("Export",core.export_report)),
        ],max_children=4,min_children=1));root.append(diag)

        con=card();con.append(label("اتصال کنسول","section-title"));con.append(label("Hotspot مستقل است و فقط با اقدام صریح روشن می‌شود. تست فیزیکی game/country یک gate جداست.","muted"))
        con.append(flow([
            button("وضعیت",lambda *_:self.run_async("Console Status",core.console_status,self.console_done)),
            button("آماده‌سازی",self.confirm_console_prepare),
            button("▶ اتصال کنسول",self.confirm_console_start,"primary"),
            button("توقف",lambda *_:self.run_async("Console Stop",core.console_stop,self.console_done),"danger"),
        ],max_children=4,min_children=1))
        self.console_label=label("در حال بررسی…","muted");con.append(self.console_label);root.append(con)

        br=card();br.append(label("Tor / Bridges","section-title"))
        br.append(flow([
            button("Tor Direct",lambda *_:self.run_async("Tor Direct",lambda:legacy.start_tor("direct"))),
            button("Tor obfs4",lambda *_:self.run_async("Tor obfs4",lambda:legacy.start_tor("obfs4"))),
            button("Tor Snowflake",lambda *_:self.run_async("Tor Snowflake",lambda:legacy.start_tor("snowflake"))),
            button("توقف Tor",lambda *_:self.run_async("Tor Stop",legacy.stop_tor),"danger"),
            button("Import obfs4",self.import_bridges),
            button("Import Snowflake",self.import_snowflake),
        ],max_children=3,min_children=1))
        self.bridge_label=label("—","muted");br.append(self.bridge_label);root.append(br)

        logs=card();logs.append(label("خروجی عملیات","section-title"))
        self.details=Gtk.TextView();self.details.set_editable(False);self.details.set_monospace(True);self.details.set_direction(Gtk.TextDirection.LTR);self.details.get_buffer().set_text("No operation has started.")
        ds=Gtk.ScrolledWindow();ds.set_min_content_height(180);ds.set_child(self.details);logs.append(ds)
        logs.append(flow([button("کپی نتیجه",self.copy_details),button("پوشه شواهد",self.open_evidence)],max_children=2,min_children=1));root.append(logs)
        return scroll(root)

    def build_settings(self):
        root=vbox(12);root.set_margin_bottom(12);root.append(self.page_head("تنظیمات","ظاهر، حریم خصوصی، تست و مسیر شخصی"))

        s=core.settings()
        ui=card();ui.append(label("ظاهر و IP","section-title"))
        tr=hbox(8);tr.append(label("تم"));self.theme_drop=Gtk.DropDown.new_from_strings(["Dark","Light"]);self.theme_drop.set_selected(0 if s["theme"]=="dark" else 1);tr.append(self.theme_drop);ui.append(tr)
        ir=hbox(8);ir.append(label("نمایش IP عمومی"));self.show_ip_switch=Gtk.Switch();self.show_ip_switch.set_active(bool(s["showIp"]));self.show_ip_switch.connect("notify::active",self.settings_ip_changed);ir.append(self.show_ip_switch);ir.append(label("فوری اعمال می‌شود","muted"));ui.append(ir);root.append(ui)

        test=card();test.append(label("تنظیمات تست","section-title"));test.append(label("BASE = اینترنت فعلی سیستم بدون ورود به provider. SELECTED = خود روش انتخاب‌شده.","muted"))
        p=hbox(8);p.append(label("مسیر تست پیش‌فرض"));self.test_path=Gtk.DropDown.new_from_strings(["BASE · اینترنت فعلی سیستم","SELECTED · روش انتخاب‌شده"]);self.test_path.set_selected(0 if s["testPathMode"]=="BASE" else 1);p.append(self.test_path);test.append(p)
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
        mr=flow(max_children=2,min_children=1)
        a=hbox(7);a.append(label("بررسی دوره‌ای"));self.monitor_switch=Gtk.Switch();self.monitor_switch.set_active(bool(s["monitor"]));a.append(self.monitor_switch);mr.append(a)
        b=hbox(7);b.append(label("Auto-repair محدود Tor"));self.repair_switch=Gtk.Switch();self.repair_switch.set_active(bool(s["autoRepair"]));b.append(self.repair_switch);mr.append(b);mon.append(mr);root.append(mon)
        root.append(button("ذخیره سایر تنظیمات",self.save_settings,"primary"))
        return scroll(root)

    def show_page(self,name):
        if self.stack:self.stack.set_visible_child_name(name)
        for k,b in self.nav.items():
            if k==name:b.add_css_class("suggested-action")
            else:b.remove_css_class("suggested-action")
        if name=="nodes":self.refresh_nodes()

    def scope_toggled(self,scope,b):
        if b.get_active():self.set_scope(scope)

    def set_scope(self,scope,widget=None):
        self.scope=scope
        names={"BROWSER":"مرورگر","SYSTEM":"کل سیستم","CONSOLE":"کنسول"}
        self.sidebar_scope.set_text("Scope: "+names.get(scope,scope))
        for k,buttons in self.scope_buttons.items():
            for b in buttons:
                want=(k==scope)
                if b.get_active()!=want:b.set_active(want)
        if hasattr(self,"methods_current"):
            title=next((x[1] for x in METHODS if x[0]==self.method),self.method)
            self.methods_current.set_text(f"{title} · {names.get(scope,scope)}")
        if scope=="CONSOLE":self.status_detail.set_text("Console Gateway مستقل انتخاب شد.")
        elif scope=="SYSTEM":self.status_detail.set_text("Full System در Linux R11 فقط WARP رسمی است.")
        else:self.status_detail.set_text("Browser scope پیش‌فرض امن است.")
        return False

    def method_toggle(self,key,b):
        if not b.get_active():return
        self.select_method(key)

    def select_method(self,key):
        self.method=key
        for k,pairs in self.method_cards.items():
            for c,b in pairs:
                want=(k==key)
                if b.get_active()!=want:b.set_active(want)
                if want:c.add_css_class("card-selected")
                else:c.remove_css_class("card-selected")
        title=next((x[1] for x in METHODS if x[0]==key),key)
        self.sidebar_method.set_text("Method: "+title)
        if hasattr(self,"selected_method_label"):self.selected_method_label.set_text("روش انتخاب‌شده: "+title)
        if hasattr(self,"methods_current"):
            names={"BROWSER":"مرورگر","SYSTEM":"کل سیستم","CONSOLE":"کنسول"}
            self.methods_current.set_text(f"{title} · {names.get(self.scope,self.scope)}")

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

    def test_base(self,ping_only=False):
        self.run_async("Base Internet "+("Ping" if ping_only else "Ping + Speed"),lambda:core.benchmark_direct(ping_only),lambda r:self.metric_done("DIRECT",r))

    def test_selected(self,ping_only):
        self.select_method(self.method)
        self.run_async(("Ping " if ping_only else "Benchmark ")+self.method,lambda:core.benchmark_method(self.method,ping_only),lambda r,m=self.method:self.metric_done(m,r))

    def test_method(self,method,ping_only=False):
        self.select_method(method)
        self.run_async(("Ping " if ping_only else "Benchmark ")+method,lambda:core.benchmark_method(method,ping_only),lambda r,m=method:self.metric_done(m,r))

    def test_all_methods(self,ping_only=False):
        self.run_async("Test All Methods · "+("Ping" if ping_only else "Full"),lambda:core.benchmark_all_methods(ping_only),self.all_methods_done)

    def all_methods_done(self,result):
        for item in result.get("results",[]) if isinstance(result,dict) else []:
            method=str(item.get("method") or "")
            if method:self.metric_done(method,item)
        if isinstance(result,dict) and result.get("error"):
            self.status_detail.set_text(str(result.get("error")))

    def metric_done(self,method,result):
        self.metrics[method]=result
        p=result.get("pingMs");d=result.get("downloadMbps");u=result.get("uploadMbps")
        fmt=f"Ping {p if p is not None else '—'} · Down {d if d is not None else '—'} · Up {u if u is not None else '—'}"
        for met in self.method_metric.get(method,[]):met.set_text(fmt)
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
        idx=int(getattr(self,"node_sort_idx",0))
        def key(n):
            ep=n.get("endpoint_test") or {};perf=n.get("performance_test") or {}
            if idx==1:return float(ep.get("latency_ms") or 999999)
            if idx==2:return -float(perf.get("downloadMbps") or 0)
            if idx==3:return -float(perf.get("uploadMbps") or 0)
            if idx==4:return str(perf.get("country") or n.get("country") or "ZZ")
            if idx==5:return str(n.get("protocol") or "")
            if idx==6:return str(n.get("name") or "").lower()
            return (0 if n.get("pinned") else 1,0 if n.get("favorite") else 1,0 if ep.get("reachable") else 1,float(ep.get("latency_ms") or 999999),-float(perf.get("downloadMbps") or 0))
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
                stats=label(
                    f"Ping: {'—' if lat is None else str(lat)+' ms'} · ↓ {'—' if perf.get('downloadMbps') is None else str(perf.get('downloadMbps'))+' Mbps'} · ↑ {'—' if perf.get('uploadMbps') is None else str(perf.get('uploadMbps'))+' Mbps'} · کشور: {perf.get('country') or '—'}",
                    "muted",xalign=0.0
                )
                stats.set_size_request(330,-1);box.append(stats)
                if n.get("id")==selected:box.add_css_class("card-selected")
                row.set_child(box);self.node_list.append(row)
            self.node_summary.set_text(f"{len(rows)} نود نمایش داده می‌شود · کل {len(core.node_store()['nodes'])} · selected={selected[:8] if selected else '—'}")
        return False

    def node_sort_toggled(self,idx,b):
        if self._syncing_sort:return
        if b.get_active():
            self.set_node_sort(idx)
        elif int(idx)==int(self.node_sort_idx):
            self._syncing_sort=True
            try:b.set_active(True)
            finally:self._syncing_sort=False

    def set_node_sort(self,idx):
        idx=max(0,min(6,int(idx)))
        self._syncing_sort=True
        try:
            self.node_sort_idx=idx
            for i,b in enumerate(self.node_sort_buttons):
                want=(i==idx)
                if b.get_active()!=want:b.set_active(want)
        finally:
            self._syncing_sort=False
        self.refresh_nodes()

    def node_row_selected(self,_list,row):
        if not row:return
        self.selected_node_id=getattr(row,"node_id","")
        n=next((x for x in self.node_cache if x.get("id")==self.selected_node_id),None)
        if not n:return
        try:
            core.node_select(self.selected_node_id)
            self.status_detail.set_text("نود انتخاب شد: "+str(n.get("name") or self.selected_node_id[:8]))
        except Exception as e:
            self.status_detail.set_text(str(e))
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

    def _apply_show_ip(self,active):
        if self._syncing_ip:return
        self._syncing_ip=True
        try:
            core.save_settings({"showIp":bool(active)})
            if hasattr(self,"dashboard_ip_switch") and self.dashboard_ip_switch.get_active()!=bool(active):self.dashboard_ip_switch.set_active(bool(active))
            if hasattr(self,"show_ip_switch") and self.show_ip_switch.get_active()!=bool(active):self.show_ip_switch.set_active(bool(active))
            self.refresh_snapshot()
        finally:
            self._syncing_ip=False

    def dashboard_ip_changed(self,sw,*_):
        self._apply_show_ip(sw.get_active())

    def settings_ip_changed(self,sw,*_):
        self._apply_show_ip(sw.get_active())

    def direct_update_clicked(self,*_):
        self.run_async("Check Update",core.update_check,self.direct_update_checked)

    def direct_update_checked(self,result):
        self.update_done(result)
        if not result.get("ok"):return
        if not result.get("updateAvailable"):
            self.status_detail.set_text("همین نسخه آخرین Linux release است.")
            return
        asset=result.get("linuxAsset") or {}
        name=str(asset.get("name") or "نسخه جدید")
        self.confirm("نصب مستقیم آپدیت",f"{name} دانلود، SHA-256 بررسی و نصب شود؟",lambda:self.run_async("Install Update",core.update_install))

    def auto_update_check_once(self):
        if not self.busy:self.run_async("Update Check",core.update_check,self.update_done)
        return False

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
