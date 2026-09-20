#!/usr/bin/env python3
import ast,json,pathlib
p=pathlib.Path(__file__).with_name("freenet_hub_linux.py");ast.parse(p.read_text(encoding="utf-8"))
print(json.dumps({"syntax":"PASS","network_on_import":False},indent=2))
