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
