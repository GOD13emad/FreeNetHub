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

hy = n.parse_uri("hysteria2://secret@hy.example.com:443?security=tls&sni=hy.example.com#SG-HY2")
assert hy["protocol"] == "hysteria2" and hy["password"] == "secret"
hycfg = n.sing_box_config(hy, 19460)
assert hycfg["outbounds"][0]["type"] == "hysteria2" and hycfg["outbounds"][0]["tls"]["enabled"] is True

try:
    n.parse_uri("tuic://x@example.com:443")
    raise AssertionError("unsupported protocol must fail closed")
except ValueError as e:
    assert str(e) == "NODE_PROTOCOL_UNSUPPORTED"

# R28 transport-compatibility regressions.
tr_default_tls = n.parse_uri("trojan://secret@tr2.example.com:443?sni=tr2.example.com#TR-DEFAULT-TLS")
assert tr_default_tls["tls"]["enabled"] is True and tr_default_tls["tls"]["server_name"] == "tr2.example.com"

ws_ed = n.parse_uri("vless://33333333-3333-3333-3333-333333333333@ed.example.com:443?security=tls&type=ws&host=cdn.example.com&path=%2Fws&ed=2560&eh=Sec-WebSocket-Protocol#WS-ED")
assert ws_ed["transport"]["type"] == "ws"
assert ws_ed["transport"]["max_early_data"] == 2560
assert ws_ed["transport"]["early_data_header_name"] == "Sec-WebSocket-Protocol"

ws_path_ed = n.parse_uri("vless://44444444-4444-4444-4444-444444444444@ed2.example.com:443?security=tls&type=ws&path=%2Fedge%3Fed%3D2048#WS-PATH-ED")
assert ws_path_ed["transport"]["path"] == "/edge"
assert ws_path_ed["transport"]["max_early_data"] == 2048
assert ws_path_ed["transport"]["early_data_header_name"] == "Sec-WebSocket-Protocol"

legacy_tr = n.parse_uri("trojan://secret@legacy.example.com:443?sni=legacy.example.com&ws=1&wspath=%2Fgo&host=cdn.example.com#LEGACY-WS")
assert legacy_tr["tls"]["enabled"] is True
assert legacy_tr["transport"]["type"] == "ws" and legacy_tr["transport"]["path"] == "/go"

http_vl = n.parse_uri("vless://55555555-5555-5555-5555-555555555555@http.example.com:443?security=tls&type=tcp&headerType=http&host=a.example.com,b.example.com&path=%2Fh2#HTTP")
assert http_vl["transport"]["type"] == "http" and http_vl["transport"]["host"] == ["a.example.com","b.example.com"]

hu = n.parse_uri("vless://66666666-6666-6666-6666-666666666666@hu.example.com:443?security=tls&type=httpupgrade&host=cdn.example.com&path=%2Fup#HU")
assert hu["transport"]["type"] == "httpupgrade" and hu["transport"]["host"] == "cdn.example.com"

print("NODEHUB_UNIT_TEST=PASS")
