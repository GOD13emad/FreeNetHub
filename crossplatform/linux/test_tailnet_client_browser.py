#!/usr/bin/env python3
"""Offline, no-desktop, no-network acceptance of the R25 Linux peer browser."""
import ast
import io
import json
import pathlib
import socket
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tailnet_client_browser as client

GOOD = {
    "BackendState": "Running",
    "Self": {"TailscaleIPs": ["100.80.5.112"], "Online": True},
    "Peer": {
        "one": {"HostName": "aliemad-Labtop", "Online": True,
                "OS": "linux", "TailscaleIPs": ["100.115.125.114"]},
        "win": {"HostName": "Emad-PC", "Online": True,
                "OS": "windows", "TailscaleIPs": ["100.90.20.11"]},
        "offline": {"HostName": "Old-Linux", "Online": False,
                    "OS": "linux", "TailscaleIPs": ["100.90.25.25"]},
    },
}
PEER = "100.115.125.114"
DOMAINS = "google.com\ncloud.google.com"


class FakeSocket:
    def __init__(self, response=b"\x05\x00" + b"\x05\x00\x00\x01" +
                 b"\x7f\x00\x00\x01\x01\xbb"):
        self.buffer = io.BytesIO(response)
        self.sent = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closed = True

    def settimeout(self, _):
        pass

    def sendall(self, data):
        self.sent.append(data)

    def recv(self, n):
        return self.buffer.read(n)


class ClientAcceptance(unittest.TestCase):
    def test_pac_executes_exact_selected_and_bypasses_unselected(self):
        node=shutil.which("node")
        if not node:self.skipTest("Node.js unavailable for PAC execution")
        pac=client.pac_source(PEER,DOMAINS)
        source = (
            "function dnsDomainIs(host, suffix) { return host.endsWith(suffix); }\n"
            + pac +
            "let selected=FindProxyForURL('https://console.cloud.google.com/', 'CONSOLE.CLOUD.GOOGLE.COM');\n"
            "let root=FindProxyForURL('https://google.com/', 'google.com.');\n"
            "let bypass=FindProxyForURL('https://example.org/', 'example.org');\n"
            "let spoof=FindProxyForURL('https://notgoogle.com/', 'notgoogle.com');\n"
            "if (!selected.startsWith('SOCKS5 100.') || root!==selected || bypass!=='DIRECT' || spoof!=='DIRECT')process.exit(4);\n"
            "console.log('PAC_SELECTIVE_BRANCHING_PASS');"
        )
        p=subprocess.run([node,"-e",source],capture_output=True,text=True,timeout=5)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("PAC_SELECTIVE_BRANCHING_PASS",p.stdout)

    def test_peer_discovery_online_linux_only(self):
        with mock.patch.object(client.gateway, "tailscale_status", return_value=GOOD):
            r = client.discover()
        self.assertTrue(r["ok"])
        self.assertEqual(r["peers"], [{"ip": PEER, "name": "aliemad-Labtop"}])
        self.assertFalse(r["settingsChanged"])

    def test_peer_offline_win_and_foreign_rejected(self):
        for addr in ("100.90.20.11", "100.90.25.25",
                     "127.0.0.1", "192.168.1.10", "100.80.5.112",
                     "https://100.115.125.114", "100.130.1.1"):
            with self.subTest(addr=addr):
                with self.assertRaises((client.ClientError, client.gateway.TailnetError)):
                    client._linux_online_peer(addr, GOOD)

    def test_duplicate_identity_refused_without_auto_selection(self):
        state = json.loads(json.dumps(GOOD))
        state["Peer"]["dup"] = dict(state["Peer"]["one"])
        with mock.patch.object(client.gateway, "tailscale_status", return_value=state):
            r = client.discover()
        self.assertFalse(r["ok"])
        self.assertIn("DUPLICATE", r["error"])

    def test_unauthenticated_socks5_probe_domain_remote_dns(self):
        sock = FakeSocket()
        with mock.patch.object(client.gateway, "tailscale_status", return_value=GOOD), \
             mock.patch.object(client.socket, "create_connection", return_value=sock) as connected:
            r = client.preflight(PEER, DOMAINS)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["probeHost"], "google.com")
        connected.assert_called_once_with((PEER, client.PORT), timeout=client.SOCKS_TIMEOUT)
        self.assertEqual(sock.sent[0], b"\x05\x01\x00")
        self.assertEqual(sock.sent[1][:4], b"\x05\x01\x00\x03")
        self.assertIn(b"google.com", sock.sent[1])
        self.assertTrue(sock.closed)

    def test_remote_socks_denies_domain_fails_closed(self):
        sock = FakeSocket(b"\x05\x00\x05\x02\x00\x01\x00\x00\x00\x00\x00\x00")
        with mock.patch.object(client.gateway, "tailscale_status", return_value=GOOD), \
             mock.patch.object(client.socket, "create_connection", return_value=sock):
            r = client.preflight(PEER, DOMAINS)
        self.assertFalse(r["ok"])
        self.assertIn("DOMAIN_CONNECT_REFUSED", r["error"])

    def test_socks_requires_noauth_and_ends_on_bad_reply(self):
        with mock.patch.object(client.socket, "create_connection",
                               return_value=FakeSocket(b"\x05\xff")):
            with self.assertRaises(client.ClientError):
                client._connect_check(PEER, "google.com")

    def test_pac_exact_suffix_no_direct_fallback(self):
        script = client.pac_source(PEER, DOMAINS)
        self.assertIn("SOCKS5 " + PEER + ":" + str(client.PORT), script)
        self.assertIn("return 'DIRECT'", script)
        self.assertNotIn("; DIRECT", script)
        self.assertIn("dnsDomainIs(host", script)
        self.assertNotIn("https://", script)
        self.assertNotIn("192.168.", script)
        self.assertEqual(client._target("https://console.cloud.google.com/apis/credentials",
                                        ["google.com", "cloud.google.com"]),
                         "https://console.cloud.google.com/apis/credentials")

    def test_url_and_domain_guards(self):
        for raw in ("https://example.org", "http://google.com",
                    "https://user:pw@google.com/", "https://google.com:8443",
                    "https://google.com\\n@example.org", "file:///etc/passwd",
                    "https://127.0.0.1/", "https://google.com/#fragment"):
            with self.subTest(url=raw):
                with self.assertRaises(client.ClientError):
                    client._target(raw, ["google.com"])
        for raw in ("*", "*.com", "localhost", "192.168.1.1",
                    "127.0.0.1", "google.com\nexample.local"):
            with self.subTest(domains=raw):
                with self.assertRaises(client.ClientError):
                    client._domains(raw)

    def test_invalid_peer_refused_before_browser_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            with mock.patch.object(client.legacy, "firefox_profile_root", return_value=root):
                r = client.launch("192.168.0.1", "google.com")
            self.assertFalse(r["ok"])
            self.assertFalse((root / client.PROFILE_NAME).exists())

    def test_owned_browser_profile_writes_only_when_preflight_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            sock = FakeSocket()
            fake_process = mock.Mock()
            fake_process.poll.return_value = None
            with mock.patch.object(client.gateway, "tailscale_status", return_value=GOOD), \
                 mock.patch.object(client.socket, "create_connection", return_value=sock), \
                 mock.patch.object(client.legacy, "firefox_profile_root", return_value=root), \
                 mock.patch.object(client.legacy, "executable", return_value="/usr/bin/firefox"), \
                 mock.patch.object(client.legacy, "project_firefox_pids", return_value=[3333]), \
                 mock.patch.object(client.subprocess, "Popen", return_value=fake_process) as started:
                # An active own browser profile must not be overwritten.
                denied = client.launch(PEER, DOMAINS)
                self.assertFalse(denied["ok"])
                self.assertIn("PROFILE_BUSY", denied["error"])
                self.assertFalse((root / client.PROFILE_NAME / client.PAC_NAME).exists())
            with mock.patch.object(client.gateway, "tailscale_status", return_value=GOOD), \
                 mock.patch.object(client.socket, "create_connection", return_value=FakeSocket()), \
                 mock.patch.object(client.legacy, "firefox_profile_root", return_value=root), \
                 mock.patch.object(client.legacy, "executable", return_value="/usr/bin/firefox"), \
                 mock.patch.object(client.legacy, "project_firefox_pids", return_value=[3333]), \
                 mock.patch.object(client.subprocess, "Popen", return_value=fake_process) as started:
                # Actual process check is consulted again; simulate idle then live.
                with mock.patch.object(client.legacy, "project_firefox_pids",
                                       side_effect=[[], [3333]]):
                    result = client.launch(PEER, DOMAINS)
                self.assertTrue(result["ok"], result)
                argv = started.call_args.args[0]
                self.assertEqual(argv[0], "/usr/bin/firefox")
                self.assertIn("--no-remote", argv)
                self.assertNotIn("--headless", argv)
                profile = root / client.PROFILE_NAME
                self.assertEqual(profile.stat().st_mode & 0o777, 0o700)
                self.assertEqual((profile / "user.js").stat().st_mode & 0o777, 0o600)
                self.assertEqual((profile / client.PAC_NAME).stat().st_mode & 0o777, 0o600)
                prefs = (profile / "user.js").read_text()
                self.assertIn('network.proxy.type", 2', prefs)
                self.assertIn('network.proxy.autoconfig_url", "file:', prefs)
                self.assertIn('network.proxy.socks_remote_dns", true', prefs)
                self.assertFalse(result["systemProxyChanged"])

    def test_failure_restores_only_prior_project_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            profile = root / client.PROFILE_NAME
            profile.mkdir()
            (profile / client.PAC_NAME).write_text("prior-owned-pac")
            (profile / "user.js").write_text("prior-owned-preferences")
            (profile / "places.sqlite").write_text("sensitive-browser-history-dummy")
            with mock.patch.object(client.gateway, "tailscale_status", return_value=GOOD), \
                 mock.patch.object(client.socket, "create_connection", return_value=FakeSocket()), \
                 mock.patch.object(client.legacy, "firefox_profile_root", return_value=root), \
                 mock.patch.object(client.legacy, "executable", return_value="/usr/bin/firefox"), \
                 mock.patch.object(client.legacy, "project_firefox_pids", return_value=[]), \
                 mock.patch.object(client.subprocess, "Popen", side_effect=OSError("launcher fails")):
                result = client.launch(PEER, DOMAINS)
            self.assertFalse(result["ok"])
            self.assertEqual((profile / client.PAC_NAME).read_text(), "prior-owned-pac")
            self.assertEqual((profile / "user.js").read_text(), "prior-owned-preferences")
            self.assertEqual((profile / "places.sqlite").read_text(), "sensitive-browser-history-dummy")

    def test_unverified_live_firefox_never_reverts_fail_closed_pac(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            proc = mock.Mock()
            proc.poll.return_value = None
            with mock.patch.object(client.gateway,"tailscale_status",return_value=GOOD), \
                 mock.patch.object(client.socket,"create_connection",return_value=FakeSocket()), \
                 mock.patch.object(client.legacy,"firefox_profile_root",return_value=root), \
                 mock.patch.object(client.legacy,"executable",return_value="/usr/bin/firefox"), \
                 mock.patch.object(client.legacy,"project_firefox_pids",return_value=[]), \
                 mock.patch.object(client.subprocess,"Popen",return_value=proc), \
                 mock.patch.object(client.time,"sleep",return_value=None):
                result=client.launch(PEER,DOMAINS)
            self.assertFalse(result["ok"])
            self.assertIn("UNCERTAIN",result["error"])
            profile=root/client.PROFILE_NAME
            self.assertIn("SOCKS5 "+PEER,(profile/client.PAC_NAME).read_text())
            self.assertIn('network.proxy.type", 2',(profile/"user.js").read_text())

    def test_explicit_stop_only_owned_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / client.PROFILE_NAME).mkdir()
            with mock.patch.object(client.legacy, "firefox_profile_root", return_value=root), \
                 mock.patch.object(client.legacy, "stop_project_firefox",
                                   return_value={"ok": True, "stopped": [3333]}) as stop:
                result = client.stop_browser()
            self.assertTrue(result["ok"])
            stop.assert_called_once_with(root / client.PROFILE_NAME)


if __name__ == "__main__":
    unittest.main(verbosity=2)
