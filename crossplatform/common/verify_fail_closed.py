#!/usr/bin/env python3
from pathlib import Path
import json, plistlib, re, sys

R=Path(__file__).resolve().parents[1]
issues=[]

android_service=(R/"android/app/src/main/java/com/freenethub/mobile/FreeNetVpnService.kt").read_text(encoding="utf-8-sig")
android_code="\n".join(line for line in android_service.splitlines() if not line.strip().startswith("//"))
android_gradle=(R/"android/app/build.gradle.kts").read_text(encoding="utf-8-sig")
android_ui=(R/"android/app/src/main/java/com/freenethub/mobile/MainActivity.kt").read_text(encoding="utf-8-sig")
if "providerCoreReady(): Boolean = false" not in android_code: issues.append("ANDROID_CORE_READY_NOT_FALSE")
if re.search(r"\.establish\s*\(",android_code): issues.append("ANDROID_TUN_ESTABLISH_ENABLED")
if 'versionCode=420' not in android_gradle or 'versionName="4.2.0"' not in android_gradle: issues.append("ANDROID_VERSION_DRIFT")
if "FreeNet Hub 4.2.0" not in android_ui: issues.append("ANDROID_UI_VERSION_DRIFT")

provider=(R/"ios/PacketTunnel/PacketTunnelProvider.swift").read_text(encoding="utf-8-sig")
ios_ui=(R/"ios/FreeNetHub/ContentView.swift").read_text(encoding="utf-8-sig")
project=(R/"ios/project.yml").read_text(encoding="utf-8-sig")
if "completionHandler(ProviderError.coreNotLinked)" not in provider: issues.append("IOS_CORE_NOT_FAIL_CLOSED")
if "setTunnelNetworkSettings" in provider: issues.append("IOS_TUN_SETTINGS_ENABLED_WITHOUT_CORE")
if "FreeNet Hub 4.2.0" not in ios_ui: issues.append("IOS_UI_VERSION_DRIFT")
if project.count("MARKETING_VERSION: 4.2.0") != 2 or project.count("CURRENT_PROJECT_VERSION: 420") != 2: issues.append("IOS_PROJECT_VERSION_DRIFT")

with (R/"ios/PacketTunnel/Info.plist").open("rb") as f:
    info=plistlib.load(f)
ext=info.get("NSExtension",{})
if ext.get("NSExtensionPointIdentifier")!="com.apple.networkextension.packet-tunnel": issues.append("IOS_EXTENSION_POINT_INVALID")
for rel in ("ios/PacketTunnel/PacketTunnel.entitlements","ios/FreeNetHub/FreeNetHub.entitlements"):
    with (R/rel).open("rb") as f: ent=plistlib.load(f)
    vals=ent.get("com.apple.developer.networking.networkextension",[])
    if "packet-tunnel-provider" not in vals: issues.append("IOS_ENTITLEMENT_INVALID:"+rel)

out={
  "schema":1,
  "android":{"version":"4.2.0","providerCoreReady":False,"tunEstablishEnabled":False},
  "ios":{"version":"4.2.0","packetTunnelCoreLinked":False,"tunnelSettingsEnabled":False,"extensionPoint":"com.apple.networkextension.packet-tunnel","entitlement":"packet-tunnel-provider"},
  "issues":issues,
  "status":"PASS" if not issues else "FAIL"
}
print(json.dumps(out,indent=2))
sys.exit(0 if not issues else 1)
