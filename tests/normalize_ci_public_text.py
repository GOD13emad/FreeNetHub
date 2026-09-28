#!/usr/bin/env python3
from pathlib import Path
R=Path(__file__).resolve().parent.parent
FILES=[
"docs/HELP_FA.txt",
"docs/RELEASE_NOTES_FA.txt",
"evidence/R21_LIVE_NODE_ACCEPTANCE_20260928.json",
"evidence/R21_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json",
"evidence/R22_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json",
"evidence/R23_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json",
"evidence/R24_SHADOWSHARE_REFRESH_ACCEPTANCE_20260928.json",
"evidence/R24_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json",
"evidence/R27_INSTALL_ACCEPTANCE_20260928.json",
"evidence/R27_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json",
"gateway/manifest.json",
"PROJECT_BRAIN.md",
]
changed=[]
for rel in FILES:
 p=R/rel
 if not p.is_file(): raise SystemExit("MISSING:"+rel)
 b=p.read_bytes()
 n=b.replace(b"\r\n",b"\n")
 if n!=b:
  p.write_bytes(n);changed.append(rel)
print("LF_NORMALIZED="+str(len(changed)))
for x in changed: print(x)
