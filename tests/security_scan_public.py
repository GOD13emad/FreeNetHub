from pathlib import Path
import re, json, sys
R=Path(__file__).resolve().parent.parent
forbidden=[]
hits=[]
binary_ext={".exe",".dll",".ico",".png",".jpg",".jpeg",".zip",".pdf"}

path_patterns=[
    ("windows_user_path", re.compile(r"C:\\\\Users\\\\(?!<USER>)[A-Za-z0-9._-]+\\\\", re.I)),
    ("linux_home_path", re.compile(r"/home/[A-Za-z0-9._-]+/")),
    ("github_token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("private_key_pem", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("wireguard_private_key", re.compile(r"(?im)^\s*PrivateKey\s*=\s*[A-Za-z0-9+/]{40,}={0,2}\s*$")),
    ("json_private_key_value", re.compile(r'(?i)"private_key"\s*:\s*"[A-Za-z0-9+/]{32,}={0,2}"')),
]
for f in R.rglob("*"):
    if not f.is_file() or ".git" in f.parts:
        continue
    rel=f.relative_to(R).as_posix()
    low=rel.lower()
    if low=="app/dependencies.json" or low.startswith("gateway/runtime/") or low.startswith("backup/") or low.startswith("delivery/") or (low.startswith("data/") and low!="data/.gitkeep") or (low.startswith("jobs/") and low!="jobs/.gitkeep"):
        forbidden.append(rel)
    if f.suffix.lower() in binary_ext or f.stat().st_size>4_000_000:
        continue
    try:
        text=f.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        continue
    for name,rx in path_patterns:
        for m in rx.finditer(text):
            sample=m.group(0)
            if name=="json_private_key_value" and rel=="gateway/tests/test_gateway.py" and "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" in sample:
                continue
            hits.append({"file":rel,"pattern":name,"match":sample[:120]})
result={"forbiddenRuntimeArtifacts":forbidden,"sensitivePatternHits":hits,"pass":not forbidden and not hits}
print(json.dumps(result,indent=2))
sys.exit(0 if result["pass"] else 1)
