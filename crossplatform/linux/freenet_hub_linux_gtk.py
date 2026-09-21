#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, pathlib, sys, threading
import gi
gi.require_version("Gtk","4.0")
from gi.repository import Gtk, GLib

APPDIR=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("fnh_backend",APPDIR/"freenet_hub_linux.py")
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class App(Gtk.Application):
    def __init__(self):super().__init__(application_id="local.freenethub")
    def do_activate(self):
        self.pending_token=None
        self.win=Gtk.ApplicationWindow(application=self,title=f"FreeNet Hub {b.VERSION}")
        self.win.set_default_size(980,640)
        root=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12)
        for fn in ("set_margin_top","set_margin_bottom","set_margin_start","set_margin_end"):getattr(root,fn)(20)
        title=Gtk.Label(label="FreeNet Hub");title.set_xalign(0);title.add_css_class("title-1");root.append(title)
        sub=Gtk.Label(label=f"Linux · explicit connection only · WARP {b.WARP_GUARD_SECONDS}s anti-lockout trial");sub.set_xalign(0);root.append(sub)
        self.status=Gtk.Label(label="Ready — choose an action explicitly.");self.status.set_xalign(0);root.append(self.status)
        row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6);root.append(row)
        actions=[("Direct status",lambda:b.trace()),("Tor status",b.tor_status),("Start Tor",b.start_tor),("Stop Tor",b.stop_tor),("WARP status",b.warp_status),("Disconnect WARP",b.warp_disconnect)]
        for label,fn in actions:
            btn=Gtk.Button(label=label);btn.connect("clicked",self.run_action,fn,label);row.append(btn)
        wb=Gtk.Button(label="Connect WARP");wb.connect("clicked",self.confirm_warp);row.append(wb)
        kb=Gtk.Button(label="Keep WARP");kb.connect("clicked",self.keep_warp);row.append(kb)
        sc=Gtk.ScrolledWindow();sc.set_vexpand(True)
        self.view=Gtk.TextView();self.view.set_editable(False);self.view.set_monospace(True);sc.set_child(self.view);root.append(sc)
        self.win.set_child(root);self.win.present()
        self.write({"version":b.VERSION,"gui":"GTK4","warp_cli":b.exists("warp-cli"),"tor":b.exists("tor"),"obfs4proxy":b.exists("obfs4proxy"),"snowflake_client":b.exists("snowflake-client"),"owned_tor":bool(b.owner())})
    def write(self,obj):
        buf=self.view.get_buffer();end=buf.get_end_iter();buf.insert(end,json.dumps(obj,ensure_ascii=False,indent=2)+"\n\n")
    def run_action(self,_btn,fn,label):
        self.status.set_text(f"Running: {label}…")
        def work():
            try:r=fn()
            except Exception as e:r={"ok":False,"error":repr(e)}
            if r.get("guard",{}).get("token"):self.pending_token=r["guard"]["token"]
            GLib.idle_add(self.done,r)
        threading.Thread(target=work,daemon=True).start()
    def confirm_warp(self,_btn):
        dialog=Gtk.MessageDialog(transient_for=self.win,modal=True,buttons=Gtk.ButtonsType.YES_NO,message_type=Gtk.MessageType.QUESTION,text=f"Connect WARP as a {b.WARP_GUARD_SECONDS}-second safe trial? It auto-disconnects unless Keep WARP is confirmed.")
        def response(d,r):
            d.destroy()
            if r==Gtk.ResponseType.YES:self.run_action(None,b.warp_connect,"Connect WARP")
        dialog.connect("response",response);dialog.present()
    def keep_warp(self,_btn):
        if not self.pending_token:
            self.done({"ok":False,"error":"no pending safe-trial token"});return
        self.run_action(None,lambda:b.warp_keep(self.pending_token),"Keep WARP")
    def done(self,r):
        self.write(r);self.status.set_text("PASS" if r.get("ok") else "Needs attention");return False

if __name__=="__main__":
    b.STATE.mkdir(parents=True,exist_ok=True)
    raise SystemExit(App().run(sys.argv))
