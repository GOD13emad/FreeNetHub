#!/usr/bin/env python3
import base64
import importlib.util
import json
import pathlib

p = pathlib.Path(__file__).parents[1] / "app" / "nodehub.py"
spec = importlib.util.spec_from_file_location("fnh_nodehub", p)
n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n)

def b64(s):
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")

ss = "ss://" + b64("aes-128-gcm:secret") + "@example.com:443#DE-SS"
vm = "vmess://" + b64(json.dumps({
    "v":"2","ps":"US-VM","add":"vm.example.com","port":"443",
    "id":"11111111-1111-1111-1111-111111111111","aid":"0","scy":"auto",
    "net":"ws","host":"cdn.example.com","path":"/ws","tls":"tls","sni":"vm.example.com"
}))
vl = "vless://22222222-2222-2222-2222-222222222222@vl.example.com:443?security=reality&type=tcp&sni=www.example.com&fp=chrome&pbk=PUBKEY&sid=abcd&flow=xtls-rprx-vision#JP-VLESS"
tr = "trojan://p%40ss@tr.example.com:443?security=tls&type=grpc&sni=tr.example.com&serviceName=svc#SG-TROJAN"

a = n.parse_uri(ss)
assert a["protocol"] == "ss" and a["method"] == "aes-128-gcm" and a["password"] == "secret"
b = n.parse_uri(vm)
assert b["protocol"] == "vmess" and b["transport"]["type"] == "ws" and b["tls"]["enabled"] is True
c = n.parse_uri(vl)
assert c["protocol"] == "vless" and c["tls"]["reality"]["public_key"] == "PUBKEY" and c["flow"] == "xtls-rprx-vision"
d = n.parse_uri(tr)
assert d["protocol"] == "trojan" and d["password"] == "p@ss" and d["transport"]["type"] == "grpc"

blob = "\n".join([ss, vm, vl, tr, ss])
r = n.parse_blob(blob, "unit")
assert r["found"] == 4 and len(r["nodes"]) == 4
wrapped = base64.b64encode(blob.encode()).decode()
r2 = n.parse_blob(wrapped, "base64")
assert r2["found"] == 4

merged = n.merge([dict(a, favorite=True, last_test={"country":"DE","healthy":True})], [a, b])
aa = next(x for x in merged if x["id"] == a["id"])
assert aa["favorite"] is True and aa["last_test"]["country"] == "DE"

cfg = n.sing_box_config(c, 19460)
assert cfg["inbounds"][0]["type"] == "socks"
assert cfg["inbounds"][0]["listen"] == "127.0.0.1"
assert cfg["inbounds"][0]["listen_port"] == 19460
assert cfg["outbounds"][0]["type"] == "vless"
assert cfg["outbounds"][0]["tls"]["reality"]["enabled"] is True
assert cfg["route"]["final"] == "provider"

pub = n.public_node(a)
assert "password" not in pub and "uuid" not in pub

try:
    n.parse_uri("hysteria2://x@example.com:443")
    raise AssertionError("unsupported protocol must fail closed")
except ValueError as e:
    assert str(e) == "NODE_PROTOCOL_UNSUPPORTED"

print("NODEHUB_UNIT_TEST=PASS")
