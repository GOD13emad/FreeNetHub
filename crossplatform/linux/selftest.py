#!/usr/bin/env python3
import importlib.util,json,pathlib
root=pathlib.Path(__file__).resolve().parent
p=root/"freenet_hub_linux.py"
s=importlib.util.spec_from_file_location("fnh",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
required=[
 "connect_mode","stop_all","warp_connect_safe","warp_keep","warp_disconnect",
 "start_tor","stop_tor","open_browser","console_prepare","console_start","console_stop",
 "doctor","speed_sample","export_report","inventory","import_snowflake","recover_stale_project_listener"
]
missing=[x for x in required if not callable(getattr(m,x,None))]
assert not missing, missing
assert m.VERSION=="4.2.0-linux.4"
assert m.WARP_GUARD_SECONDS==60
def public_bridge_lines(name):
    p=root/name
    return [x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip() and not x.lstrip().startswith("#")]
assert not public_bridge_lines("bridges_obfs4.txt"), "public obfs4 template must not contain active bridge material"
assert not public_bridge_lines("bridges_snowflake.txt"), "public Snowflake template must not contain active bridge material"
print(json.dumps({
 "ok":True,"version":m.VERSION,"missing":missing,"network_on_import":False,
 "warp_guard_seconds":m.WARP_GUARD_SECONDS,
 "ui":"GTK4+Libadwaita","desktop_id":"local.freenethub",
 "public_bridge_material":False
},indent=2))
