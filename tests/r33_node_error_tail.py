import pathlib,re,json
p=pathlib.Path.home()/"AppData/Local/Programs/FreeNetHub/data/NODE/stderr.log"
lines=p.read_text(encoding="utf-8",errors="replace").splitlines()[-500:]
def s(x):
 x=re.sub(r"\x1b\[[0-9;]*m","",x)
 x=re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F-]{20,}","<UUID>",x)
 x=re.sub(r"(?<![A-Za-z0-9_-])(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?","<IP>",x)
 x=re.sub(r"(?i)([a-z0-9-]+\.)+[a-z]{2,}","<HOST>",x)
 x=re.sub(r"(?i)(password|uuid|public[_ -]?key|short[_ -]?id|private[_ -]?key)[=: ]+\S+",r"\1=<REDACTED>",x)
 return re.sub(r"\s+"," ",x).strip()[:360]
out=[s(x) for x in lines if ("ERROR" in x or "WARN" in x)]
print(json.dumps({"count":len(out),"tail":out[-80:]},ensure_ascii=False,indent=2))
