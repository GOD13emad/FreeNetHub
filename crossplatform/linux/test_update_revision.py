import importlib.util, json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("fnh_r43_update_test", HERE/"freenet_hub_linux_r37.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

assert m.VERSION=="4.2.0-linux.19-r46"
assert m._linux_revision_from_version(m.VERSION)==19
assert m._linux_revision_from_version("4.2.0-linux.99-r123")==99
assert m._linux_revision_from_version("broken") is None
assert m._linux_revision_from_name("FreeNetHub_4.2.0_Linux_R16.zip")==16
assert m._linux_revision_from_name("FreeNetHub_4.2.0_Linux_R17.zip")==17
assert m._linux_revision_from_name("FreeNetHub_4.2.0_Linux_R18.zip")==18
assert m._linux_revision_from_name("FreeNetHub_4.2.0_R41_Diagnostic.exe") is None

class FakeResponse:
    def __init__(self,payload): self.payload=payload
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,n=-1): return json.dumps(self.payload).encode("utf-8")

def payload(revision):
    return {"tag_name":f"v4.2.0-r{revision+27}-final","published_at":"2026-10-05T00:00:00Z","assets":[
      {"name":f"FreeNetHub_4.2.0_Linux_R{revision}.zip","size":123,"digest":"sha256:"+"a"*64,"browser_download_url":f"https://github.com/GOD13emad/FreeNetHub/releases/download/x/FreeNetHub_4.2.0_Linux_R{revision}.zip"},
      {"name":"FreeNetHub_4.2.0_R99_Diagnostic.exe","size":1,"digest":"sha256:"+"b"*64,"browser_download_url":"https://github.com/GOD13emad/FreeNetHub/releases/download/x/FreeNetHub_4.2.0_R99_Diagnostic.exe"}
    ]}

orig=m.urllib.request.urlopen
try:
    m.urllib.request.urlopen=lambda *a,**k: FakeResponse(payload(19))
    same=m.update_check()
    assert same["ok"] and same["localRevision"]==19 and same["remoteRevision"]==19 and same["updateAvailable"] is False
    m.urllib.request.urlopen=lambda *a,**k: FakeResponse(payload(20))
    newer=m.update_check()
    assert newer["ok"] and newer["localRevision"]==19 and newer["remoteRevision"]==20 and newer["updateAvailable"] is True
    saved=m.VERSION
    m.VERSION="broken"
    broken=m.update_check()
    assert broken["ok"] is False and broken["error"]=="LOCAL_LINUX_REVISION_UNPARSEABLE"
    m.VERSION=saved
finally:
    m.urllib.request.urlopen=orig
print("linux update revision regression: PASS")
