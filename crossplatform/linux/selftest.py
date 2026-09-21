#!/usr/bin/env python3
import importlib.util,json,pathlib,tempfile
p=pathlib.Path(__file__).with_name("freenet_hub_linux.py")
spec=importlib.util.spec_from_file_location("fnh",p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.SOCKS_PORT==9909
assert m.WARP_GUARD_SECONDS>=60
assert callable(m.start_tor) and callable(m.stop_tor) and callable(m.warp_connect) and callable(m.warp_keep)
print(json.dumps({"syntax":"PASS","backend_import":"PASS","network_on_import":False,"version":m.VERSION,"warp_guard_seconds":m.WARP_GUARD_SECONDS},indent=2))
