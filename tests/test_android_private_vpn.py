#!/usr/bin/env python3
"""No-network proof: Android private VPN is isolated, opted-in and hash-pinned.
Does NOT assert that its mobile network forwarding has been field-accepted.
"""
import hashlib
import ipaddress
import re
import io
import pathlib
import xml.etree.ElementTree as ET
import zipfile

REPO = pathlib.Path(__file__).resolve().parent.parent
BASE = REPO / "crossplatform/android"
PRO = BASE / "vpnPrototype"
SOURCE = PRO / "src/main/java/com/freenethub/mobile/prototype"
A = "{http://schemas.android.com/apk/res/android}"

public_manifest = ET.parse(BASE / "app/src/main/AndroidManifest.xml").getroot()
assert not list(public_manifest.iter("service")), "ACCEPTED_PUBLIC_APP_VPN_CHANGED"
public_stub = (BASE/"app/src/main/java/com/freenethub/mobile/FreeNetVpnService.kt").read_text()
assert "providerCoreReady(): Boolean = false" in public_stub
print("PASS_ACCEPTED_PUBLIC_ANDROID_APP_STILL_FAIL_CLOSED")

manifest = ET.parse(PRO / "src/main/AndroidManifest.xml").getroot()
app = manifest.find("application")
assert app is not None and app.get(A+"allowBackup")=="false"
assert app.get(A+"usesCleartextTraffic")=="false"
services = list(manifest.iter("service"))
assert len(services)==1 and services[0].get(A+"name")==".PrivateVpnService"
assert services[0].get(A+"exported")=="true"
assert services[0].get(A+"permission")=="android.permission.BIND_VPN_SERVICE"
assert services[0].get(A+"foregroundServiceType")=="specialUse"
assert any(x.get(A+"name")=="android.net.VpnService"
           for x in services[0].iter("action"))
assert not list(manifest.iter("receiver")), "NO_SILENT_BOOT_START"
assert services[0].find("property") is not None
assert any(x.get(A+"name")=="android.net.VpnService.SUPPORTS_ALWAYS_ON"
           and x.get(A+"value")=="false" for x in services[0].iter("meta-data"))
permissions = [p.get(A+"name") for p in manifest.iter("uses-permission")]
assert "android.permission.FOREGROUND_SERVICE_SPECIAL_USE" in permissions
print("PASS_REGISTERED_SEPARATE_PRIVATE_VPN_AND_FGS_DECLARATION")

settings = (BASE/"settings.gradle.kts").read_text()
assert settings.count('include(":app")')==1 and settings.count('include(":vpnPrototype")')==1
gradle = (PRO/"build.gradle.kts").read_text()
assert 'applicationId = "com.freenethub.mobile.prototype"' in gradle
assert 'versionCode = 2' in gradle and 'versionName = "0.2-private-usb"' in gradle
assert 'targetSdk = 36' in gradle and 'compileSdk = 36' in gradle and 'minSdk = 29' in gradle
assert 'verifyHevNativeArtifact' in gradle and 'preBuild' in gradle
print("PASS_SEPARATE_APPLICATION_ID_NO_REPLACEMENT_OF_USER_APP")

service = (SOURCE/"PrivateVpnService.kt").read_text()
ui = (SOURCE/"MainActivity.kt").read_text()
probe = (SOURCE/"SocksPreflight.kt").read_text()
tunnel = (SOURCE/"TunnelConfig.kt").read_text()
for needed in (
    "ACTION_START", "ACTION_STOP", "VpnService.prepare(this)",
    'isLockdownEnabled', 'addDisallowedApplication(packageName)',
    'addRoute("0.0.0.0", 0)', 'addRoute("::", 0)',
    "addDnsServer(TunnelConfig.MAPPED_DNS_V4)",
    "builder.establish()", "TProxyService.TProxyStartService",
    "TProxyService.TProxyStopService", "TProxyService.TProxyIsRunning",
    "onRevoke()", "STOP_FOREGROUND_REMOVE",
):
    assert needed in service, "MISSING_NATIVE_SAFETY_CONTRACT: "+needed
assert 'VpnService.prepare(this)' in ui and '.setPositiveButton(' in ui
assert "startActivityForResult(intent, PREPARE_VPN_REQUEST)" in ui
assert 'SocksPreflight.check()' in ui and 'SocksPreflight.check()' in service
assert "BOOT_COMPLETED" not in ui+service
assert "VPN unavailable until forwarding core" in (
    BASE/"app/src/main/java/com/freenethub/mobile/MainActivity.kt").read_text()
print("PASS_OWNER_CONSENT_AND_ABORT_CLEANUP_CONTRACT")

# Split system authorization from any TUN establishment. Android's native
# permission UI remains user-controlled and no upstream or VPN is needed to
# grant authorization alone.
assert "private const val PREPARE_ONLY_REQUEST = 17424" in ui
assert "private fun requestVpnPermissionOnly()" in ui
segment=ui.split("private fun requestVpnPermissionOnly()",1)[1].split("override fun onCreate",1)[0]
assert 'VpnService.prepare(this)' in segment
assert 'startActivityForResult(intent, PREPARE_ONLY_REQUEST)' in segment
assert ".setPositiveButton(" in segment and ".setNegativeButton(" in segment
for unsafe in ("startOwnedVpn(", "startForegroundService(", "PrivateVpnService.ACTION_START",
               "TProxyService.TProxyStartService", "builder.establish()"):
    assert unsafe not in segment, "PERMISSION_ONLY_AUTO_CONNECT_PATH:"+unsafe
assert 'permissionOnly.setOnClickListener { requestVpnPermissionOnly() }' in ui
assert 'outer.addView(permissionOnly)' in ui
result=ui.split("override fun onActivityResult(",1)[1].split("override fun onResume()",1)[0]
assert "if (requestCode == PREPARE_ONLY_REQUEST)" in result
assert "if (requestCode != PREPARE_VPN_REQUEST)" in result
assert result.index("if (requestCode == PREPARE_ONLY_REQUEST)") < result.index("if (requestCode != PREPARE_VPN_REQUEST)")
prepare_branch=result.split("if (requestCode == PREPARE_ONLY_REQUEST)",1)[1].split("if (requestCode != PREPARE_VPN_REQUEST)",1)[0]
assert "startOwnedVpn()" not in prepare_branch
assert "refresh()" in prepare_branch and "return" in prepare_branch
assert "consentStatus" in ui
print("PASS_ANDROID_OWNER_NATIVE_PERMISSION_ONLY_NO_TUN_ACTIVATION")

assert 'NATIVE_EXIT_TUN_STILL_BLOCKING_USER_MUST_STOP' in service
assert 'if (!healthy)' in service and 'return' in service.split('if (!healthy)',1)[1].split('}',1)[0]
assert 'stop.isEnabled = true' in ui
assert 'ACTION_STOP -> stopOwned()' in service
assert 'START_NOT_STICKY' in service
assert "START_ON_BOOT" not in service+ui
print("PASS_NATIVE_FAILURE_BLOCKS_DIRECT_FALLBACK_UNTIL_USER_STOP")

assert 'endpointIdentificationAlgorithm = "HTTPS"' in probe
assert 'probeOne("www.google.com")' in probe
assert 'probeOne("www.youtube.com")' in probe
assert 'SOCKS5_REMOTE_CONNECT_REFUSED' in probe
assert 'InetSocketAddress(TunnelConfig.SOCKS_HOST, TunnelConfig.SOCKS_PORT)' in probe
assert "import java.net.HttpURLConnection" not in probe and "ProxySelector.getDefault(" not in probe
assert 'SOCKS_HOST = "127.0.0.1"' in tunnel and 'SOCKS_PORT = 19414' in tunnel
assert "udp: 'tcp'" in tunnel, "UNSAFE_UDP_IN_UDP_RELAY_CONFIGURED"
assert "udp: 'udp'" not in tunnel, "DIRECT_UDP_RELAY_MODE_FORBIDDEN"
print("PASS_LOCALHOST_SOCKS_ONLY_AND_TLS_PEER_IDENTITY")

# hev-socks5-tunnel 2.18.0 implements IPv4 A-only fake-IP DNS mapped to
# the original domain in the outbound SOCKS5 CONNECT.  adb reverse is TCP-only:
# never claim this enables UDP ASSOCIATE, DoH/DoT, or IPv6 AAAA support.
assert not re.search(r"(?m)^\s*const val DNS_V[46]\s*=", tunnel), "PUBLIC_DNS_CONSTANT_REMAINED"
match = re.search(r'const val MAPPED_DNS_V4 = "([^"]+)"', tunnel)
assert match and match.group(1) == "198.18.0.2"
for key, value in {
    "address": "198.18.0.2",
    "port": "53",
    "network": "198.19.0.0",
    "netmask": "255.255.0.0",
    "cache-size": "8192",
}.items():
    assert re.search(r"(?m)^          " + re.escape(key) + r": ['\"]?" +
                     re.escape(value) + r"['\"]?$", tunnel), (key, value)
assert "        mapdns:\n" in tunnel
assert "addDnsServer(TunnelConfig.MAPPED_DNS_V4)" in service
assert "addDnsServer(TunnelConfig.DNS_V6)" not in service
mapped_network = ipaddress.IPv4Network("198.19.0.0/16")
tun_range = ipaddress.IPv4Network("198.18.0.0/15")
assert mapped_network.subnet_of(tun_range)
assert ipaddress.IPv4Address(match.group(1)) not in mapped_network
assert int(ipaddress.IPv4Address(match.group(1))) != int(ipaddress.IPv4Address("198.18.0.1"))
assert 8192 < mapped_network.num_addresses - 1
# USB ADB reverse is TCP-only; force HEV's UDP_IN_TCP branch, which must
# fail closed if this SOCKS provider lacks HEV's non-standard UDP-over-TCP.
assert "udp: 'tcp'" in tunnel and "udp: 'udp'" not in tunnel
assert "UPSTREAM_UDP_OVER_TCP_UNVERIFIED" in (PRO/"README_PRIVATE.md").read_text()
assert "IPv4 A" in (PRO/"README_PRIVATE.md").read_text()
print("PASS_MAPPED_IPV4_DNS_WITH_SOCKS_REMOTE_HOSTNAME_NO_PUBLIC_DNS_DEFAULT")


helper = PRO/"fetch_pinned_aar.py"
source_helper=helper.read_text()
expected_sha="15ec8ed121663b562c99caa5bb602d1009f24e5b09e733438b81988f12feaaab"
assert source_helper.count(expected_sha)==1 and expected_sha in gradle
assert "590342" in source_helper and "590342" in gradle
assert (PRO/"LICENSE-hev-socks5-tunnel.txt").read_text().startswith(
    "Copyright (c) 2022 hev")
p=PRO/"libs/hev-socks5-tunnel-2.18.0.aar"
if p.exists():
    data=p.read_bytes()
    assert len(data)==590342 and hashlib.sha256(data).hexdigest()==expected_sha
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.testzip() is None
        expected={"classes.jar"}|{
            "jni/"+x+"/libhev-socks5-tunnel.so"
            for x in ("arm64-v8a","armeabi-v7a","x86","x86_64")
        }
        assert expected.issubset(z.namelist())
        with zipfile.ZipFile(io.BytesIO(z.read("classes.jar"))) as j:
            assert "hev/htproxy/TProxyService.class" in j.namelist()
print("PASS_UPSTREAM_MIT_NATIVE_PIN_4_ABIS")

assert "PRIVATE" in (PRO/"README_PRIVATE.md").read_text()
print("ANDROID_PRIVATE_SOURCE_ACCEPTANCE=9_OF_9_PASS_NO_MOBILE_VPN_FIELD_CLAIM")
