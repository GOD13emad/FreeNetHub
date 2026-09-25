#!/usr/bin/env python3
import importlib.util, json, pathlib, tempfile
root=pathlib.Path(__file__).resolve().parent
p=root/"freenet_hub_linux.py"
spec=importlib.util.spec_from_file_location("fnh_console_policy",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class P:
    def __init__(self, rc=0, out="", err=""):
        self.returncode=rc; self.stdout=out; self.stderr=err

calls=[]
old={
 "console_status":m.console_status,
 "nm_connection_uuids":m.nm_connection_uuids,
 "console_owned_uuid":m.console_owned_uuid,
 "run":m.run,
 "executable":m.executable,
 "CONSOLE":m.CONSOLE,
}
with tempfile.TemporaryDirectory(prefix="fnh-console-policy-") as td:
    m.CONSOLE=pathlib.Path(td)/"console.json"
    m.CONSOLE.write_text(json.dumps({
        "created_by":m.APP,
        "connection_name":m.CONSOLE_NAME,
        "connection_uuid":"OWNED-UUID",
        "device":"wlan-test",
        "type":"wifi",
        "ssid":m.CONSOLE_NAME,
        "password":"LegacySecret1234",
        "gateway":"192.168.77.1",
        "client_ip":"192.168.77.2",
        "subnet":"192.168.77.0/24",
    })+"\n",encoding="utf-8")
    m.executable=lambda name: "/usr/bin/nmcli" if name=="nmcli" else old["executable"](name)
    m.console_status=lambda:{"ok":True,"candidates":[{"device":"wlan-test","type":"wifi"}]}
    m.nm_connection_uuids=lambda name=m.CONSOLE_NAME:["OWNED-UUID"]
    m.console_owned_uuid=lambda cfg=None:"OWNED-UUID"
    def fake_run(args, timeout=0, **kwargs):
        calls.append(list(args))
        return P()
    m.run=fake_run
    try:
        result=m.console_prepare()
        saved=json.loads(m.CONSOLE.read_text(encoding="utf-8"))
        first_password=saved.get("password")
        calls.clear()
        result2=m.console_prepare()
        saved2=json.loads(m.CONSOLE.read_text(encoding="utf-8"))
        second_password=saved2.get("password")
    finally:
        for k,v in old.items(): setattr(m,k,v)

modify=next((c for c in calls if "modify" in c),[])
def has_pair(k,v):
    return any(modify[i]==k and i+1 < len(modify) and modify[i+1]==v for i in range(len(modify)))
out={
 "ok":bool(
   result.get("ok")
   and has_pair("wifi-sec.key-mgmt","wpa-psk")
   and has_pair("wifi-sec.proto","rsn")
   and has_pair("wifi-sec.pmf","disable")
   and "password" not in (result.get("config") or {})
   and "password" not in (result2.get("config") or {})
   and first_password=="LegacySecret1234"
   and second_password==first_password
 ),
 "version":m.VERSION,
 "key_mgmt":"wpa-psk",
 "proto":m.CONSOLE_WIFI_PROTO,
 "pmf":m.CONSOLE_WIFI_PMF,
 "password_redacted":"password" not in (result.get("config") or {}),
 "password_stable_across_prepare":second_password==first_password=="LegacySecret1234",
}
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["ok"] else 2)
