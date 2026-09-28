#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,pathlib
P=pathlib.Path(__file__).resolve().parent.parent/'app'/'engine.py'
spec=importlib.util.spec_from_file_location('eng_r26',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
h=m.node_endpoint_probe({'protocol':'hysteria2','server':'127.0.0.1','port':9})
assert h['reachable'] is None
assert h['type']=='UDP_QUIC_PREFLIGHT_NOT_APPLICABLE'
print('R26_HY2_PREFLIGHT_POLICY=PASS')
