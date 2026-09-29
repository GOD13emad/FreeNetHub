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
 "BrowserConnectCard","FullSystemConnectCard","ConsoleConnectCard","Mode","Country",
 "MainTest","MainConnect","AdvancedMethodsOpen","MainSelectionSummary","ConnectionScopeText",
 "MainMethodSmart","MainMethodNode","MainMethodWarp","MainMethodCfon","MainMethodTor","MainMethodCustom","MainMethodDirect",
 "SidebarScope","SidebarMethod","SidebarTargetCountry","TestMethodValue","TestStateValue","UpdateRootPath",
 "ConnectSmart","TestSmart","ConnectNode","TestNodePath","ConnectWarp","TestWarpPath",
 "ConnectCfon","TestCfonPath","ConnectTor","TestTorPath","ConnectCustom","TestCustomPath",
 "NodeList","NodeRefreshPublic","NodeRefreshList","NodeTestAll","NodeBenchmarkBatch","NodeSpeed",
 "ConsoleSpeed","ConsoleCapability","GatewaySetupConsole","UpdateCheckMain","UpdateInstallMain","UpdateStatus","ToolsNodeRefresh","DirectNetworkAudit","DirectDpiStart","DirectDpiStop","DirectDpiStatus"
}
assert not sorted(required-names), "UX controls missing: "+", ".join(sorted(required-names))

for binding in ("Status","Name","Country","Protocol","Ping","Download","Upload","Source","LastTest"):
    assert f'Binding="{{Binding {binding}}}"' in xaml, "Node DataGrid column missing: "+binding

headers=re.findall(r'<TabItem Header="([^"]+)"',xaml)
assert headers==["⌂  داشبورد اتصال","⌘  روش‌های اتصال","◉  نودها / سرورها","⚒  ابزارها و آپدیت","⚙  تنظیمات"], headers
assert 'داشبورد اتصال' in xaml
assert 'روش‌های اتصال' in xaml
assert 'Header="⚙  تنظیمات"' in xaml

for step in ("انتخاب نوع اتصال","انتخاب روش اتصال","تست قبل از اتصال"):
    assert step in xaml, "connection workflow step missing: "+step
assert 'Text="۴"' in xaml and 'Text="اتصال"' in xaml

assert "تست قبل از اتصال" in xaml
assert "MethodCardButton" in xaml
assert "CONNECTION CENTER" in xaml
assert "مسیر پایهٔ سیستم برای آپدیت: فعال" in xaml
assert "آپدیت از مسیر سیستم" in xaml
assert "Node Pool" in xaml
assert "Ping + Download + Upload" in xaml
assert "$script:ConnectionScope='BROWSER'" in ps
assert "Select-ConnectionScope" in ps
assert "Paint-ConnectionSelection" in ps
assert "Tabs.SelectedIndex -eq 2" in ps
assert "AdvancedMethodsOpen.Add_Click({$script:C.Tabs.SelectedIndex=1})" in ps
assert "ConsoleOpenCard.Add_Click({$script:C.Tabs.SelectedIndex=3})" in ps
assert "NextNodeRefresh" in ps and "NextNodeBenchmark" in ps
assert "UpdateInstallMain" in ps
for resource in ("SelectedFill","PillFill","TableHeader","UpdatePanel"):
    assert resource in xaml and resource in ps, "theme-aware resource missing: "+resource
assert "ConsolePreflight" in ps
assert "NodeSystemPreflight" in ps
assert "Persistent-SelectedNodeId" in ps
assert "Start-Work 'SystemSpeed' 'WARP'" not in ps
assert "Paint-Performance $r.result 'WARP'" not in ps
assert "NODE','WARP" in ps or "NODE','WARP')" in ps

assert "Console-Capability" in ps and "Paint-ConsoleCapability" in ps
assert "GatewaySetupConsole.Add_Click" in ps
assert "$script:Pythonw" in ps and "Get-Command pythonw.exe" in ps
assert "Start-Work 'ProviderBenchmark' $provider" in ps
assert "Resolve-SystemProvider" in ps
assert "@('AUTO','NODE','WARP')" in ps
assert "$script:C.Country.IsEnabled=" in ps and "$countryCapable" in ps
assert "ConvertFromString('#102238')" not in ps
assert 'Background="#102238"' not in xaml
print(f"R29_UX_CONTRACT=PASS refs={len(refs)} names={len(names)} tab_count={len(headers)}")

assert "Connect-MethodCard" in ps and "$script:C.ConnectSmart.Add_Click({Connect-MethodCard 'AUTO'})" in ps
assert "Start-ConfiguredTest" in ps and "$script:C.MainTest.Add_Click({Start-ConfiguredTest $false})" in ps
assert "ToolsTestBasePath.Add_Click" in ps and "testPathMode='BASE'" in ps and "testPathMode='SELECTED'" in ps
assert "PingTimeoutBox.Add_SelectionChanged" in ps and "downloadTimeoutSec" in ps and "uploadTimeoutSec" in ps
assert "Invoke-DirectDpi" in ps and "FreeNetHub\\directdpi\\state.json" in ps
