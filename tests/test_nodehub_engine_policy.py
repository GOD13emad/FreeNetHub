#!/usr/bin/env python3
import importlib.util
import pathlib
import tempfile
from unittest.mock import patch

p = pathlib.Path(__file__).parents[1] / "app" / "engine.py"
spec = importlib.util.spec_from_file_location("fnh_engine_node_policy", p)
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)

nodes = [
    {"id":"de1","name":"DE fast","protocol":"vless","favorite":False,"pinned":False,"last_test":{},"endpoint_test":{"reachable":True,"latency_ms":20}},
    {"id":"us1","name":"US backup","protocol":"trojan","favorite":False,"pinned":False,"last_test":{},"endpoint_test":{"reachable":True,"latency_ms":30}},
]
selected = {"id": None}
events = []

def store():
    return {"schema":1,"selected":selected["id"] or "de1","nodes":[dict(x) for x in nodes]}

def select(node_id):
    selected["id"] = node_id
    events.append(("select", node_id))
    return next(x for x in nodes if x["id"] == node_id)

def ensure(mode):
    events.append(("ensure", mode, selected["id"]))
    return {"healthy":True,"mode":"NODE","country":"DE","ip":"203.0.113.20","seconds":0.2,"checked":"2026-09-28T00:00:00+00:00","error":""}

with patch.object(E, "node_store", side_effect=store),      patch.object(E, "node_batch_fast", return_value={"total":2,"reachable":2}),      patch.object(E, "node_select", side_effect=select),      patch.object(E, "node_record_test", side_effect=lambda *a, **k: None),      patch.object(E, "owned", return_value={"nodeId":"old"}),      patch.object(E, "stop", side_effect=lambda mode: events.append(("stop", mode)) or True),      patch.object(E, "ensure", side_effect=ensure):
    h = E.ensure_node("DE", limit=1)
    assert h["healthy"] is True and h["country"] == "DE"
    assert events[0] == ("stop", "NODE")
    assert ("select", "de1") in events

with patch.object(E, "country_target", return_value="DE"):
    with patch.object(E, "settings", return_value=E.DEFAULT | {"country":"DE","order":["NODE","WARP","CFON"]}):
        assert E.connect_candidates("AUTO") == ["NODE","CFON"]
        assert E.connect_candidates("NODE") == ["NODE"]

with tempfile.TemporaryDirectory() as td:
    old_root = E.ROOT
    try:
        E.ROOT = pathlib.Path(td)
        (E.ROOT / "jobs").mkdir(parents=True)
        f = E.ROOT / "jobs" / "node-import-test.txt"
        f.write_text("ss://YWVzLTEyOC1nY206c2VjcmV0@example.com:443#DE", encoding="utf-8")
        with patch.object(E, "node_import_text", return_value={"imported":1,"nodes":[]}):
            r = E.dispatch("NodeImport", "AUTO", str(f))
        assert r["imported"] == 1 and not f.exists()
    finally:
        E.ROOT = old_root

with patch.object(E, "node_store", return_value={"schema":1,"selected":"de1","nodes":[nodes[0]]}),      patch.object(E, "node_selected", return_value=nodes[0]),      patch.object(E, "owned", return_value=None),      patch.object(E, "ensure", return_value={"healthy":True,"mode":"NODE","country":"DE","ip":"203.0.113.21","seconds":0.3,"checked":"2026-09-28T00:00:00+00:00","error":""}),      patch.object(E, "node_record_test", return_value=None),      patch.object(E, "stop", return_value=True):
    r = E.dispatch("NodeTest", "NODE", "")
    assert "test" in r and r["test"]["healthy"] is True
    assert r["temporary"] is True
    assert "healthy" not in {k for k in r if k != "test"}

source = p.read_text(encoding="utf-8")
assert "'nodeId':node_selected().get('id')" in source
assert "NODE_ACTIVE_STOP_FIRST" in source
assert "node-id.txt" in source

print("NODEHUB_ENGINE_POLICY_TEST=PASS")
