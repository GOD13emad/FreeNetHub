#!/usr/bin/env python3
from __future__ import annotations
import ast,pathlib
P=pathlib.Path(__file__).resolve().parent.parent/'app'/'engine.py'
s=P.read_text(encoding='utf-8')
assert "SHADOWSHARE_README_ID" in s and "SHADOWSHARE_README_BN" in s and "SHADOWSHARE_README_ES" in s
assert "'SG':('singapore','singapour','singapur')" in s
ast.parse(s)
print('R25_COUNTRY_AVAILABILITY_STATIC=PASS')
