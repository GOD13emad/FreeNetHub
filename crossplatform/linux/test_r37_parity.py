#!/usr/bin/env python3
import hashlib
import importlib.util
import pathlib

ROOT=pathlib.Path(__file__).resolve().parents[2]
LIN=ROOT/"crossplatform"/"linux"

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

legacy=load("legacy",LIN/"freenet_hub_linux.py")
assert legacy.VERSION=="4.2.0-linux.11-r37"
r37=load("r37",LIN/"freenet_hub_linux_r37.py")
assert r37.VERSION=="4.2.0-linux.11-r37"
assert r37.NODE_PORT==19460
assert r37.settings()["testPathMode"] in ("BASE","SELECTED")
for fn in ("node_store","node_refresh_public","node_test_all","node_connect","node_connect_auto","node_stop","node_raw","node_history","node_export","node_update_meta","node_benchmark_batch","benchmark_method","benchmark_configured","benchmark_all_methods","connect_method","warpplus_status","warpplus_start","update_check","update_install","open_browser"):
    assert callable(getattr(r37,fn))
ui=(LIN/"freenet_hub_linux_gtk.py").read_text(encoding="utf-8")
assert "core.benchmark_method(self.method,ping_only)" in ui
assert "core.benchmark_direct(ping_only)" in ui
for marker in ("داشبورد","روش‌ها","Node Pool","ابزارها","تنظیمات","Ping + Download + Upload","اتصال کنسول","Export Raw","Export Base64","History","Copy Raw","ذخیره Metadata","تست سریع همه روش‌ها","تست کامل همه روش‌ها","تست اولیه همه نودها","تست واقعی 4 نود برتر","مرتب‌سازی بر اساس","بیشترین Upload","کشور","نمایش IP","بررسی و نصب مستقیم آخرین نسخه"):
    assert marker in ui, marker
assert "self.win.set_size_request(720,480)" in ui
assert "self.method_cards.setdefault(key,[])" in ui
assert "self.scope_buttons.setdefault(key,[])" in ui
assert "self.node_sort_idx=0" in ui
assert "self.node_sort_toggled" in ui
assert "self._syncing_sort" in ui
assert "elif int(idx)==int(self.node_sort_idx)" in ui
assert "بیشترین Upload" in ui
installer=(LIN/"install.sh").read_text(encoding="utf-8")
for marker in ("freenet_hub_linux_r37.py","nodehub_shared.py","runtime/usr/bin/sing-box","runtime/usr/bin/warp-plus","4.2.0-linux.11-r37","install_singbox_pinned.sh","install_warpplus_pinned.sh"):
    assert marker in installer, marker
pin=(LIN/"install_singbox_pinned.sh").read_text(encoding="utf-8")
assert "v1.14.2" in pin
assert "5c7bc18461827b28d0e5ee7e89d33b276d3ff7c818531104c8e8d26d85b0656e" in pin
wp=(LIN/"install_warpplus_pinned.sh").read_text(encoding="utf-8")
assert "v1.2.6" in wp
assert "380d2c8655b33db818adf407c706d52d14c2ab1764e702e91f356a7d7d9c3c98" in wp
assert r37._linux_revision_from_name("FreeNetHub_4.2.0_Linux_R11.zip")==11
assert r37._linux_revision_from_name("bad.zip") is None

# Test-all must fail closed rather than replacing an active FreeNet Hub connection.
orig_session=r37.legacy.session
try:
    r37.legacy.session=lambda:{"mode":"TOR"}
    all_busy=r37.benchmark_all_methods(True)
    assert not all_busy["ok"] and all_busy["error"]=="STOP_FREENETHUB_CONNECTION_BEFORE_TEST_ALL"
finally:
    r37.legacy.session=orig_session

# Dashboard configured test must honor BASE without entering the selected provider.
orig_settings=r37.settings
orig_direct=r37.benchmark_direct
orig_method=r37.benchmark_method
try:
    r37.settings=lambda:{"testPathMode":"BASE"}
    r37.benchmark_direct=lambda ping_only=False:{"ok":True,"mode":"DIRECT","path":"PHYSICAL_BASE_INTERFACE","pingOnly":ping_only}
    r37.benchmark_method=lambda *_args,**_kw: (_ for _ in ()).throw(AssertionError("SELECTED_PROVIDER_CALLED_IN_BASE_MODE"))
    base=r37.benchmark_configured("WARP",True)
    assert base["ok"] and base["mode"]=="DIRECT" and base["requestedMethod"]=="WARP" and base["testPathMode"]=="BASE"
    r37.settings=lambda:{"testPathMode":"SELECTED"}
    r37.benchmark_method=lambda mode,ping_only=False:{"ok":True,"mode":mode,"pingOnly":ping_only}
    selected=r37.benchmark_configured("NODE",False)
    assert selected["ok"] and selected["mode"]=="NODE" and selected["requestedMethod"]=="NODE" and selected["testPathMode"]=="SELECTED"
finally:
    r37.settings=orig_settings
    r37.benchmark_direct=orig_direct
    r37.benchmark_method=orig_method
assert hashlib.sha256((ROOT/"app"/"nodehub.py").read_bytes()).hexdigest()==hashlib.sha256((LIN/"nodehub_shared.py").read_bytes()).hexdigest()
print("LINUX_R37_PARITY_STATIC=PASS")
