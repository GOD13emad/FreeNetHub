#!/usr/bin/env python3
import pathlib, re, xml.etree.ElementTree as ET

ROOT=pathlib.Path(__file__).parents[1]
xaml_path=ROOT/"app"/"View.xaml"
ps_path=ROOT/"app"/"FreeNetHub.ps1"
xaml=xaml_path.read_text(encoding="utf-8-sig")
ps=ps_path.read_text(encoding="utf-8-sig")
ET.fromstring(xaml)

names=set(re.findall(r'(?:Name|x:Name)="([A-Za-z0-9_]+)"',xaml))
refs=set(re.findall(r'\$script:C\.([A-Za-z0-9_]+)',ps)) - {'ContainsKey','Count'}
missing=sorted(refs-names)
assert not missing, "controller references missing from XAML: "+", ".join(missing)

required={
 "BrowserConnectCard","FullSystemConnectCard","ConsoleConnectCard","CurrentPathSpeed",
 "ConnectSmart","TestSmart","ConnectNode","TestNodePath","ConnectWarp","TestWarpPath",
 "ConnectCfon","TestCfonPath","ConnectTor","TestTorPath","ConnectCustom","TestCustomPath",
 "NodeList","NodeRefreshPublic","NodeRefreshList","NodeTestAll","NodeBenchmarkBatch","NodeSpeed",
 "ConsoleSpeed","UpdateCheckMain","UpdateInstallMain","UpdateStatus"
}
assert not sorted(required-names), "R28 controls missing: "+", ".join(sorted(required-names))

for binding in ("Status","Name","Country","Protocol","Ping","Download","Upload","Source","LastTest"):
    assert f'Binding="{{Binding {binding}}}"' in xaml, "Node DataGrid column missing: "+binding

assert "DataGrid" in xaml
assert "Ping + Download + Upload" in xaml
assert "GitHub Update" in xaml
assert "NextNodeRefresh" in ps and "NextNodeBenchmark" in ps
assert "NodeBenchmarkBatch" in ps and "AddMinutes(30)" in ps and "AddMinutes(10)" in ps
assert "UpdateInstallMain" in ps
print(f"R28_UI_CONTRACT=PASS refs={len(refs)} names={len(names)}")
