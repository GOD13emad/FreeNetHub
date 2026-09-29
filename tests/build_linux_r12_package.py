#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,zipfile
R=pathlib.Path(__file__).resolve().parent.parent
L=R/"crossplatform"/"linux"
OUT=R/"delivery"/"github_v4.2.0"/"FreeNetHub_4.2.0_Linux_R12.zip"
ROOT="FreeNetHub_4.2.0_Linux_R12"
FILES=[
 "freenet_hub_linux.py","freenet_hub_linux_r37.py","freenet_hub_linux_gtk.py","nodehub_shared.py",
 "install.sh","install_singbox_pinned.sh","install_warpplus_pinned.sh","install_warp_official.sh",
 "uninstall.sh","warp_guard.py","recover_warp_remote.sh","freenethub.desktop","FreeNetHub.svg",
 "bridges_obfs4.txt","bridges_snowflake.txt","README_FA.md","selftest.py","test_browser_profile.py",
 "test_console_policy.py","test_private_state_permissions.py","test_scope_policy.py","test_r37_parity.py"
]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest().upper()
rows=[]
for rel in FILES:
 p=L/rel
 if not p.is_file():raise SystemExit("MISSING:"+rel)
 rows.append({"file":rel,"bytes":p.stat().st_size,"sha256":sha(p)})
manifest={"schema":1,"version":"4.2.0-linux.12-r38","release":"LINUX_4.2.0_R12_R38_AUDIT_FIX","files":rows}
OUT.parent.mkdir(parents=True,exist_ok=True)
tmp=OUT.with_suffix(".tmp.zip")
with zipfile.ZipFile(tmp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for rel in sorted(FILES):
  data=(L/rel).read_bytes();zi=zipfile.ZipInfo(f"{ROOT}/{rel}",date_time=(2026,9,29,0,0,0));zi.external_attr=((0o755 if rel.endswith((".sh",".py")) else 0o644)&0xFFFF)<<16;zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,data)
 for name,obj in [
  ("PACKAGE_MANIFEST.json",manifest),
  ("SHA256SUMS.txt","".join(f'{x["sha256"]}  {x["file"]}\n' for x in rows))
 ]:
  data=(json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode() if isinstance(obj,dict) else obj.encode()
  zi=zipfile.ZipInfo(f"{ROOT}/{name}",date_time=(2026,9,29,0,0,0));zi.external_attr=(0o644&0xFFFF)<<16;zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,data)
tmp.replace(OUT)
print(json.dumps({"status":"PASS","path":str(OUT.relative_to(R)),"bytes":OUT.stat().st_size,"sha256":sha(OUT),"files":len(FILES)}))
