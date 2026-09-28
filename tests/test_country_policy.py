#!/usr/bin/env python3
import importlib.util
import pathlib

p = pathlib.Path(__file__).parents[1] / "app" / "engine.py"
spec = importlib.util.spec_from_file_location("fnh_engine_country", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def cfg(country):
    return m.DEFAULT | {"country": country, "order": ["WARP", "TOR", "GOOL", "CFON"]}

m.settings = lambda: cfg("DE")
assert m.connect_candidates("AUTO") == ["NODE", "CFON"]
assert m.connect_candidates("CFON") == ["CFON"]
assert m.connect_candidates("CUSTOM") == ["CUSTOM"]
try:
    m.connect_candidates("WARP")
    raise AssertionError("WARP must not silently ignore a strict country target")
except ValueError as e:
    assert str(e) == "COUNTRY_MODE_UNSUPPORTED"

m.settings = lambda: cfg("AUTO")
assert m.connect_candidates("AUTO") == ["WARP", "TOR", "GOOL", "CFON"]
assert m.connect_candidates("TOR") == ["TOR"]

m.settings = lambda: cfg("DE")
m.progress = lambda *args, **kwargs: None

def fake_curl_good(url, proxy="", seconds=7, body=True, size=262144):
    if "cdn-cgi/trace" in url:
        return {"exit": 0, "code": "200", "seconds": 0.1, "bytes": 64, "bps": 1000.0, "body": "ip=203.0.113.10\nloc=DE\nwarp=off\n", "error": ""}
    return {"exit": 0, "code": "204", "seconds": 0.2, "bytes": 0, "bps": 0.0, "body": "", "error": ""}

m.curl = fake_curl_good
r = m.probe("CFON", proxy="socks5h://127.0.0.1:19414")
assert r["healthy"] is True
assert r["country"] == "DE"
assert r["countryPolicy"] == "DE"

def fake_curl_bad(url, proxy="", seconds=7, body=True, size=262144):
    if "cdn-cgi/trace" in url:
        return {"exit": 0, "code": "200", "seconds": 0.1, "bytes": 64, "bps": 1000.0, "body": "ip=203.0.113.11\nloc=US\nwarp=off\n", "error": ""}
    return {"exit": 0, "code": "204", "seconds": 0.2, "bytes": 0, "bps": 0.0, "body": "", "error": ""}

m.curl = fake_curl_bad
r = m.probe("CFON", proxy="socks5h://127.0.0.1:19414")
assert r["healthy"] is False
assert r["error"] == "COUNTRY_MISMATCH_OR_UNKNOWN"
assert r["country"] == "US"
assert r["countryPolicy"] == "DE"

r = m.probe("CUSTOM", proxy="socks5h://127.0.0.1:19999")
assert r["healthy"] is False
assert r["error"] == "COUNTRY_MISMATCH_OR_UNKNOWN"

print("COUNTRY_STRICT_POLICY_TEST=PASS")


# R23 regression: strict target must reject a healthy wrong-country exit.
def test_strict_country_rejects_healthy_wrong_exit_and_accepts_match():
    calls=[]
    nodes=[{"id":"wrong","name":"stale SG","protocol":"vless","last_test":{"healthy":True,"country":"SG"},"endpoint_test":{"reachable":True,"latency_ms":20}},{"id":"match","name":"SG hint","protocol":"vless","last_test":{},"endpoint_test":{"reachable":True,"latency_ms":30}}]
    old_store,old_owned,old_stop,old_select,old_ensure,old_record,old_batch = m.node_store,m.owned,m.stop,m.node_select,m.ensure,m.node_record_test,m.node_batch_fast
    try:
        m.node_store=lambda:{"nodes":nodes}
        m.node_batch_fast=lambda:{"total":len(nodes),"reachable":len(nodes)}
        m.owned=lambda mode:None
        m.stop=lambda mode:calls.append(("stop",mode))
        m.node_select=lambda nid:calls.append(("select",nid))
        results=iter([{"healthy":True,"country":"US","error":""},{"healthy":True,"country":"SG","error":""}])
        m.ensure=lambda mode:next(results)
        m.node_record_test=lambda nid,h:calls.append(("record",nid,h.get("country"),h.get("healthy"),h.get("error")))
        h=m.ensure_node("SG",limit=2)
        assert h["healthy"] is True and h["country"]=="SG"
        assert ("stop","NODE") in calls
        assert any(x[0]=="record" and x[1]=="wrong" and x[3] is False and x[4]=="COUNTRY_MISMATCH_OR_UNKNOWN" for x in calls)
    finally:
        m.node_store,m.owned,m.stop,m.node_select,m.ensure,m.node_record_test,m.node_batch_fast = old_store,old_owned,old_stop,old_select,old_ensure,old_record,old_batch

def test_strict_country_no_match_stops_and_fails_closed():
    calls=[]
    nodes=[{"id":"wrong","name":"DE hint","protocol":"vless","last_test":{},"endpoint_test":{"reachable":True,"latency_ms":20}}]
    old_store,old_owned,old_stop,old_select,old_ensure,old_record,old_batch = m.node_store,m.owned,m.stop,m.node_select,m.ensure,m.node_record_test,m.node_batch_fast
    try:
        m.node_store=lambda:{"nodes":nodes}
        m.node_batch_fast=lambda:{"total":len(nodes),"reachable":len(nodes)}
        m.owned=lambda mode:None
        m.stop=lambda mode:calls.append(("stop",mode))
        m.node_select=lambda nid:None
        m.ensure=lambda mode:{"healthy":True,"country":"US","error":""}
        m.node_record_test=lambda nid,h:None
        try:
            m.ensure_node("DE",limit=1)
            raise AssertionError("expected NODE_COUNTRY_NOT_FOUND")
        except RuntimeError as e:
            assert str(e)=="NODE_COUNTRY_NOT_FOUND"
        assert ("stop","NODE") in calls
    finally:
        m.node_store,m.owned,m.stop,m.node_select,m.ensure,m.node_record_test,m.node_batch_fast = old_store,old_owned,old_stop,old_select,old_ensure,old_record,old_batch


test_strict_country_rejects_healthy_wrong_exit_and_accepts_match()
test_strict_country_no_match_stops_and_fails_closed()
print("R23_STRICT_NODE_COUNTRY_REGRESSION=PASS")


# R26 regression: a listener-up but broken Node must not consume the full 30s retry window.
def test_node_broken_https_fails_fast_after_two_completed_probes():
    import time as _time
    calls=[]; state={"started":False,"probes":0}
    old=(m.owned,m.start,m.port_open,m.probe,m.stop,m.check,m.progress,m.DEADLINE)
    try:
        m.owned=lambda mode: {"nodeId":"x"} if state["started"] else None
        def _start(mode,scan=False):
            state["started"]=True;calls.append(("start",mode));return {"created":0}
        m.start=_start
        m.port_open=lambda port: True
        def _probe(mode):
            state["probes"]+=1
            return {"healthy":False,"error":"HTTPS_VERIFICATION_FAILED","ip":"","country":"","seconds":None}
        m.probe=_probe
        m.stop=lambda mode:calls.append(("stop",mode)) or True
        m.check=lambda:None;m.progress=lambda *a,**k:None;m.DEADLINE=_time.monotonic()+60
        try:
            m.ensure("NODE")
            raise AssertionError("expected PATH_NOT_VERIFIED_NODE")
        except RuntimeError as ex:
            assert str(ex)=="PATH_NOT_VERIFIED_NODE"
        assert state["probes"]==2
        assert ("stop","NODE") in calls
    finally:
        m.owned,m.start,m.port_open,m.probe,m.stop,m.check,m.progress,m.DEADLINE=old

test_node_broken_https_fails_fast_after_two_completed_probes()
print("R26_NODE_FAILFAST_REGRESSION=PASS")
