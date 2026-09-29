from __future__ import annotations
import pathlib,re,json,collections,datetime
p=pathlib.Path.home()/"AppData/Local/Programs/FreeNetHub/data/NODE/stderr.log"
txt=p.read_text(encoding="utf-8",errors="replace") if p.exists() else ""
lines=txt.splitlines()[-6000:]
def sanitize(s:str)->str:
    s=re.sub(r"\x1b\[[0-9;]*m","",s)
    s=re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F-]{20,}","<UUID>",s)
    s=re.sub(r"(?<![A-Za-z0-9_-])(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?","<IP>",s)
    s=re.sub(r"(?i)([a-z0-9-]+\.)+[a-z]{2,}","<HOST>",s)
    s=re.sub(r"(?i)(password|uuid|public[_ -]?key|short[_ -]?id|private[_ -]?key)[=: ]+\S+",r"\1=<REDACTED>",s)
    s=re.sub(r"\b\d+(?:\.\d+)?(?:ms|s)\b","<TIME>",s)
    s=re.sub(r"\s+"," ",s).strip()
    return s[:320]
cats=collections.Counter()
samples={}
patterns=[
 ("tls_plaintext_or_wrong_port",r"(?i)first record does not look like a tls handshake"),
 ("tls_handshake",r"(?i)tls.*handshake|handshake.*tls"),
 ("ws_handshake",r"(?i)websocket.*(?:handshake|status|response)"),
 ("auth_rejected",r"(?i)unauthor|forbidden|authentication|bad password|invalid user|rejected"),
 ("connection_reset",r"(?i)reset by peer|connection reset|broken pipe"),
 ("connection_refused",r"(?i)connection refused"),
 ("timeout",r"(?i)timeout|deadline exceeded|i/o timeout"),
 ("dns",r"(?i)no such host|lookup .* failed|dns"),
 ("eof",r"(?i)unexpected eof|\beof\b"),
 ("reality",r"(?i)reality|short.?id|public.?key"),
 ("network_unreachable",r"(?i)network is unreachable|no route"),
]
normalized=collections.Counter()
for line in lines:
    low=line.lower()
    if not ("error" in low or "fail" in low or "warn" in low):
        continue
    sl=sanitize(line)
    matched=False
    for name,pat in patterns:
        if re.search(pat,line):
            cats[name]+=1
            samples.setdefault(name,[])
            if len(samples[name])<3:samples[name].append(sl)
            matched=True;break
    normalized[sl]+=1
out={
 "schema":1,
 "date":"2026-09-28",
 "privacy":"No raw node URI, IP, hostname, UUID, credential, key, or exit IP emitted.",
 "logBytes":p.stat().st_size if p.exists() else 0,
 "linesExamined":len(lines),
 "categories":[{"category":k,"count":v,"samples":samples.get(k,[])} for k,v in cats.most_common()],
 "topNormalized":[{"count":c,"message":m} for m,c in normalized.most_common(20)]
}
print(json.dumps(out,ensure_ascii=False,indent=2))
