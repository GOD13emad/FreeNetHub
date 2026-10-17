#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,zipfile,subprocess
R=pathlib.Path(__file__).resolve().parent.parent
L=R/"crossplatform"/"linux"
OUT=R/"delivery"/"github_v4.2.0"/"FreeNetHub_4.2.0_Linux_R25.zip"
ROOT="FreeNetHub_4.2.0_Linux_R25"
EXPECTED_VERSION="4.2.0-linux.25-r58"
EXPECTED_RELEASE="LINUX_4.2.0_R25_R58_PEER_BROWSER_SELECTIVE"
FILES=[
 "freenet_hub_linux.py","freenet_hub_linux_r37.py","freenet_hub_linux_gtk.py","nodehub_shared.py","selective_tunnel.py","tailnet_cfon_gateway.py",
 "install.sh","install_singbox_pinned.sh","install_warpplus_pinned.sh","install_warp_official.sh",
 "uninstall.sh","warp_guard.py","recover_warp_remote.sh","freenethub.desktop","FreeNetHub.svg",
 "bridges_obfs4.txt","bridges_snowflake.txt","README_FA.md","selftest.py","test_browser_profile.py",
 "test_console_policy.py","test_private_state_permissions.py","test_scope_policy.py","test_r37_parity.py",
 "test_update_revision.py","test_warp_tos_owner_consent.py","test_selective_tunnel.py","test_selective_integration.py","test_tailnet_cfon_gateway.py",
 "tailnet_client_browser.py","test_tailnet_client_browser.py"
]
# Newly versioned candidate. Preserve exact clean-filter semantics; after
# promotion CI will reconstruct the same SHA from the tested source tree.
for rel in ("freenet_hub_linux.py","freenet_hub_linux_r37.py"):
 text=(L/rel).read_text(encoding="utf-8")
 if EXPECTED_VERSION not in text:raise SystemExit("R25_VERSION_MISMATCH:"+rel)
installer=(L/"install.sh").read_text(encoding="utf-8")
if EXPECTED_VERSION not in installer or EXPECTED_RELEASE not in installer:
 raise SystemExit("R25_INSTALL_CONTRACT_CHANGED")
def canonical_bytes(p):
 path=pathlib.Path(p)
 rel=path.relative_to(R).as_posix()
 oid=subprocess.check_output(["git","hash-object","-w",f"--path={rel}",str(path)],cwd=R,text=True).strip()
 return subprocess.check_output(["git","cat-file","blob",oid],cwd=R)
def sha_bytes(data):return hashlib.sha256(data).hexdigest().upper()
rows=[];payload={}
for rel in FILES:
 p=L/rel
 if not p.is_file():raise SystemExit("MISSING:"+rel)
 data=canonical_bytes(p);payload[rel]=data
 rows.append({"file":rel,"bytes":len(data),"sha256":sha_bytes(data)})
manifest={"schema":1,"version":"4.2.0-linux.25-r58","release":"LINUX_4.2.0_R25_R58_PEER_BROWSER_SELECTIVE","files":rows}
OUT.parent.mkdir(parents=True,exist_ok=True)
tmp=OUT.with_suffix(".tmp.zip")
with zipfile.ZipFile(tmp,"w",compression=zipfile.ZIP_STORED) as z:
 for rel in sorted(FILES):
  data=payload[rel];zi=zipfile.ZipInfo(f"{ROOT}/{rel}",date_time=(2026,9,29,0,0,0));zi.external_attr=((0o755 if rel.endswith((".sh",".py")) else 0o644)&0xFFFF)<<16;zi.create_system=3;zi.compress_type=zipfile.ZIP_STORED;z.writestr(zi,data)
 for name,obj in [
  ("PACKAGE_MANIFEST.json",manifest),
  ("SHA256SUMS.txt","".join(f'{x["sha256"]}  {x["file"]}\n' for x in rows))
 ]:
  data=(json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode() if isinstance(obj,dict) else obj.encode()
  zi=zipfile.ZipInfo(f"{ROOT}/{name}",date_time=(2026,9,29,0,0,0));zi.external_attr=(0o644&0xFFFF)<<16;zi.create_system=3;zi.compress_type=zipfile.ZIP_STORED;z.writestr(zi,data)
tmp.replace(OUT)
print(json.dumps({"status":"PASS","path":str(OUT.relative_to(R)),"bytes":OUT.stat().st_size,"sha256":sha_bytes(OUT.read_bytes()),"files":len(FILES)}))
