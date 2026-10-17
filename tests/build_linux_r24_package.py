#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,zipfile,subprocess
R=pathlib.Path(__file__).resolve().parent.parent
L=R/"crossplatform"/"linux"
OUT=R/"delivery"/"github_v4.2.0"/"FreeNetHub_4.2.0_Linux_R24.zip"
ROOT="FreeNetHub_4.2.0_Linux_R24"
EXPECTED_VERSION="4.2.0-linux.24-r57"
EXPECTED_RELEASE="LINUX_4.2.0_R24_R57_OWNER_TAILNET_CFON"
FILES=[
 "freenet_hub_linux.py","freenet_hub_linux_r37.py","freenet_hub_linux_gtk.py","nodehub_shared.py","selective_tunnel.py","tailnet_cfon_gateway.py",
 "install.sh","install_singbox_pinned.sh","install_warpplus_pinned.sh","install_warp_official.sh",
 "uninstall.sh","warp_guard.py","recover_warp_remote.sh","freenethub.desktop","FreeNetHub.svg",
 "bridges_obfs4.txt","bridges_snowflake.txt","README_FA.md","selftest.py","test_browser_profile.py",
 "test_console_policy.py","test_private_state_permissions.py","test_scope_policy.py","test_r37_parity.py",
 "test_update_revision.py","test_warp_tos_owner_consent.py","test_selective_tunnel.py","test_selective_integration.py","test_tailnet_cfon_gateway.py"
]
# R24 is a frozen accepted preview. Reconstruct it only from its exact
# accepted source commit, even after the working tree moves to R25.
# In CI use a full checkout so the pinned source is available offline.
FROZEN_COMMIT="428fea704225b70b1640c5d085cf6e8e8a9ae23b"
FROZEN_SHA256="D76958F80923BFC1B77E406FE00F4CE96CC83A9A54521415DBBDAE53AFFB1824"
def canonical_bytes(p):
 rel=pathlib.Path(p).relative_to(R).as_posix()
 return subprocess.check_output(["git","show",f"{FROZEN_COMMIT}:{rel}"],cwd=R)
def sha_bytes(data):return hashlib.sha256(data).hexdigest().upper()
rows=[];payload={}
for rel in FILES:
 p=L/rel
 if not p.is_file():raise SystemExit("MISSING:"+rel)
 data=canonical_bytes(p);payload[rel]=data
 rows.append({"file":rel,"bytes":len(data),"sha256":sha_bytes(data)})
manifest={"schema":1,"version":"4.2.0-linux.24-r57","release":"LINUX_4.2.0_R24_R57_OWNER_TAILNET_CFON","files":rows}
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
if sha_bytes(OUT.read_bytes())!=FROZEN_SHA256:
 raise SystemExit("FROZEN_R24_REBUILD_SHA_MISMATCH")
print(json.dumps({"status":"PASS","path":str(OUT.relative_to(R)),"bytes":OUT.stat().st_size,"sha256":sha_bytes(OUT.read_bytes()),"files":len(FILES)}))
