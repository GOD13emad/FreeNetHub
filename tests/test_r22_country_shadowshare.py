#!/usr/bin/env python3
import importlib.util, json, pathlib, tempfile

R=pathlib.Path(__file__).parents[1]

# Static UI/controller coverage.
nh_text=(R/"app"/"nodehub.py").read_text(encoding="utf-8")
eng_text=(R/"app"/"engine.py").read_text(encoding="utf-8")
ui=(R/"app"/"View.xaml").read_text(encoding="utf-8")
ps=(R/"app"/"FreeNetHub.ps1").read_text(encoding="utf-8")

assert "function Sync-CountrySelection" in ps
assert "Country.Add_SelectionChanged({Sync-CountrySelection" in ps
assert "Write-Json (Join-Path $script:Root 'settings.json') $script:Settings" in ps
assert "$countryMismatch=[bool]" in ps
for proto in ("ss","vmess","vless","trojan"):
    assert proto in nh_text
for token in ("NodePin","NodeMeta"):
    assert token in eng_text and token in ps
for token in ("NodeFilter","NodeSort","NodeSaveMeta","NodeHistory","NodeCopyLink","NodeExportRaw","NodeExportBase64"):
    assert token in ui and token in ps
assert "hist.append(event)" in eng_text
assert "ToBase64String" in ps

# Dynamic store/action coverage without network.
spec=importlib.util.spec_from_file_location("fnh_r22_engine",R/"app"/"engine.py")
E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
with tempfile.TemporaryDirectory() as td:
    old_root=E.ROOT
    try:
        E.ROOT=pathlib.Path(td)
        (E.ROOT/"data").mkdir(parents=True)
        (E.ROOT/"jobs").mkdir(parents=True)
        node={
            "id":"n1","name":"DE node","protocol":"vless","server":"example.invalid","port":443,
            "uuid":"11111111-1111-1111-1111-111111111111","raw":"vless://secret@example.invalid:443",
            "favorite":False,"pinned":False,"rating":0,"tags":[],"note":"","source":"unit"
        }
        E.save_node_store({"schema":1,"selected":"n1","nodes":[node]})
        r=E.dispatch("NodePin","NODE","n1")
        assert r["pinned"] is True and r["nodes"][0]["pinned"] is True

        req=E.ROOT/"jobs"/"node-meta-unit.json"
        req.write_text(json.dumps({"id":"n1","name":"My DE","note":"stable","tags":["work","de"],"rating":4}),encoding="utf-8")
        r=E.dispatch("NodeMeta","NODE",str(req))
        assert not req.exists()
        pub=r["node"]
        assert pub["name"]=="My DE" and pub["rating"]==4 and pub["tags"]==["work","de"] and pub["note"]=="stable"
        assert "raw" not in pub and "uuid" not in pub

        E.node_record_test("n1",{"healthy":True,"country":"DE","ip":"203.0.113.8","seconds":0.2,"error":"","checked":"2026-09-28T00:00:00Z"})
        s=E.node_store();n=s["nodes"][0]
        assert len(n["history"])==1 and "ip" not in n["history"][0]
        public=E.NH.public_node(n)
        assert public["history"][0]["country"]=="DE"
        assert "ip" not in public["history"][0]
        assert "raw" not in public and "uuid" not in public
    finally:
        E.ROOT=old_root

assert "COUNTRY_MISMATCH_OR_UNKNOWN" in eng_text
assert "ensure_node(country_target())" in eng_text
assert "NODE_COUNTRY_NOT_FOUND" in eng_text
assert "Public shared nodes are untrusted and temporary" in eng_text
print("R22_COUNTRY_SHADOWSHARE_DYNAMIC_TEST=PASS")
