#!/usr/bin/env python3
"""Zero-impact domain-selective PAC / recovery regressions; stdlib only."""
from __future__ import annotations

import contextlib
import http.server
import pathlib
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import selective_tunnel as st


class DomainTests(unittest.TestCase):
    def test_normalization_and_canonical(self):
        self.assertEqual(st.parse_domains("BRAVE.com, *.brave.com; stripe.com\nstripe.network."),
                         ["brave.com", "stripe.com", "stripe.network"])
        self.assertEqual(st.parse_domains("bücher.example"), ["xn--bcher-kva.example"])

    def test_google_domains_403_and_custom_preservation(self):
        self.assertIn("google.com", st.GOOGLE_DOMAINS)
        self.assertIn("googleapis.com", st.GOOGLE_DOMAINS)
        self.assertGreaterEqual(len(st.GOOGLE_DOMAINS),25)
        self.assertEqual(st.merge_domains("custom.example\nbrave.com",
                         "google.com\ncustom.example"),
                         ["custom.example","brave.com","google.com"])
        self.assertEqual(st.host_from_url("https://console.cloud.google.com/apis/credentials?key=private"),
                         "console.cloud.google.com")
        for bad in ("http://google.com", "https://127.0.0.1/", "https://admin@google.com",
                    "https://google.com:1234/", "https://private.local/", "file:///root"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                st.host_from_url(bad)
        def run(args,**kwargs):
            self.assertEqual(kwargs["timeout"],11)
            self.assertIn("--head",args)
            self.assertEqual(args[-1],"https://console.cloud.google.com/")
            return subprocess.CompletedProcess(args,0,
                     "302" if "--socks5-hostname" in args else "403","")
        with mock.patch.object(st.subprocess,"run",side_effect=run):
            out=st.diagnose_403_site("https://console.cloud.google.com/apis/credentials?token=private",19414)
        self.assertEqual((out["directCode"],out["tunnelCode"]),(403,302))
        self.assertTrue(out["suggestAdd"])
        self.assertFalse(out["authenticated"])

    def test_fail_closed_input(self):
        bad = [
            "", "*", "*.com", "com", "co.uk", "127.0.0.1", "localhost", "hello.local",
            "http://example.com", "example.com:8080", '" ; return "DIRECT"', "hello..com",
            "-evil.example", "other.example/path", "foo<script>.example",
            "a" * 64 + ".example", " ".join(f"host{i}.example" for i in range(65)),
        ]
        for value in bad:
            with self.subTest(value=value[:48]), self.assertRaises(ValueError):
                st.parse_domains(value)

    def test_pac_in_node_vm(self):
        domains = ["brave.com", "bravesoftware.com", "stripe.com", "stripe.network"]
        pac = st.pac_script(domains, 19414)
        self.assertNotIn("DIRECT; SOCKS5", pac)
        self.assertIn("SOCKS5 127.0.0.1:19414", pac)
        for h in domains:
            self.assertIn('"' + h + '"', pac)
        js = """
const vm = require('vm');
const ctx={dnsDomainIs:(host,suffix)=>host.endsWith(suffix)};
vm.runInNewContext(process.argv[1],ctx);
const tests=[
 ['account.brave.com','SOCKS5 127.0.0.1:19414'],
 ['api-dashboard.search.brave.com','SOCKS5 127.0.0.1:19414'],
 ['checkout.stripe.com','SOCKS5 127.0.0.1:19414'],
 ['js.stripe.com','SOCKS5 127.0.0.1:19414'],
 ['m.stripe.network','SOCKS5 127.0.0.1:19414'],
 ['chatgpt.com','DIRECT'], ['www.google.com','DIRECT'], ['fakebrave.com','DIRECT'],
 ['evilstripe.com','DIRECT'], ['localhost','DIRECT'],
];
for(const [host,expected] of tests){
 const found=ctx.FindProxyForURL('https://'+host,host);
 if(found!==expected){console.error(host,found,expected);process.exit(2);}
}
"""
        with mock.patch.object(subprocess, "run", wraps=subprocess.run) as real:
            r = real(["node", "-e", js, pac], capture_output=True, text=True, timeout=5)
        self.assertEqual(r.returncode, 0, r.stderr)


class ProxyHealthFailClosedTests(unittest.TestCase):
    def test_socks_health_forces_proxy_despite_ambient_no_proxy(self):
        # Reproduces a real curl failure mode: NO_PROXY=* bypasses the
        # explicitly selected local SOCKS server unless --noproxy "" wins.
        observed = []
        def fake_command(args, timeout=8):
            observed.append(list(args))
            self.assertEqual(timeout, 12)
            self.assertEqual(args[0], "curl")
            self.assertIn("--socks5-hostname", args)
            i = args.index("--noproxy")
            self.assertEqual(args[i + 1], "")
            self.assertEqual(args[args.index("--socks5-hostname") + 1], "127.0.0.1:19414")
            self.assertEqual(args[-1], "https://www.cloudflare.com/cdn-cgi/trace")
            return subprocess.CompletedProcess(args, 0, "200", "")
        with (mock.patch.object(st.socket, "create_connection") as socket_check,
              mock.patch.object(st, "_command", side_effect=fake_command),
              mock.patch.dict("os.environ", {"NO_PROXY": "*", "no_proxy": "*"})):
            st._probe(19414)
        self.assertEqual(len(observed), 1)
        socket_check.assert_called_once_with(("127.0.0.1", 19414), timeout=2)

    def test_dead_socks_listener_must_not_be_accepted_as_direct_https(self):
        def fake_command(args, timeout=8):
            self.assertEqual(args[args.index("--noproxy") + 1], "")
            raise subprocess.CalledProcessError(97, args, stderr="SOCKS protocol failure")
        with (mock.patch.object(st.socket, "create_connection"),
              mock.patch.object(st, "_command", side_effect=fake_command),
              mock.patch.dict("os.environ", {"NO_PROXY": "*", "no_proxy": "*"})):
            with self.assertRaisesRegex(st.SelectiveError, "SELECTIVE_PROXY_UNREACHABLE"):
                st._probe(19414)

    def test_unreachable_socks_listener_is_rejected_before_http(self):
        with (mock.patch.object(st.socket, "create_connection",
                               side_effect=ConnectionRefusedError),
              mock.patch.object(st, "_command") as called):
            with self.assertRaisesRegex(st.SelectiveError, "SELECTIVE_PROXY_NOT_LISTENING"):
                st._probe(19414)
        called.assert_not_called()

    def test_invalid_port_rejected_before_any_network(self):
        with mock.patch.object(st.socket, "create_connection") as connect:
            for invalid in (0, 80, 65536, True, "19414"):
                with self.subTest(invalid=invalid), self.assertRaisesRegex(
                    st.SelectiveError, "SELECTIVE_PROXY_PORT_INVALID"
                ):
                    st._probe(invalid)
        connect.assert_not_called()


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fnh-selective-test-")
        self.root = pathlib.Path(self.temp.name)
        self.setting = {"mode": "auto", "autoconfig-url": "file:///owner/original.pac"}
        self.patches = [
            mock.patch.object(st, "DATA", self.root / "data"),
            mock.patch.object(st, "PAC_FILE", self.root / "data" / "route.pac"),
            mock.patch.object(st, "POLICY", self.root / "data" / "policy.json"),
            mock.patch.object(st, "SERVICE", self.root / "user" / "freenethub-selective-pac.service"),
            mock.patch.object(st, "_setting", side_effect=lambda k: self.setting[k]),
            mock.patch.object(st, "_set_setting", side_effect=lambda k, v: self.setting.__setitem__(k, v)),
            mock.patch.object(st, "_probe", return_value=None),
        ]
        for p in self.patches:
            p.start()
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), st._PACHandler)
        self.port = self.srv.server_address[1]
        self.patches.extend([
            mock.patch.object(st, "PORT", self.port),
            mock.patch.object(st, "URL", f"http://127.0.0.1:{self.port}/route.pac"),
            mock.patch.object(st, "_service_ctl", side_effect=self.service_control),
        ])
        for p in self.patches[-3:]:
            p.start()
        self.thread = None
        self.controls = []

    def service_control(self, *args):
        self.controls.append(tuple(args))
        if "enable" in args and self.thread is None:
            self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
            self.thread.start()

    def tearDown(self):
        if self.thread:
            self.srv.shutdown()
        self.srv.server_close()
        if self.thread:
            self.thread.join(timeout=3)
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def test_apply_update_noop_and_exact_restore(self):
        r = st.apply(st.DEFAULT_DOMAINS, 19414, "CFON")
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], "enabled")
        self.assertEqual(st.status()["healthy"], True)
        self.assertEqual(self.setting["mode"], "auto")
        self.assertEqual(self.setting["autoconfig-url"], st.pac_url(st.PAC_FILE.read_text()))
        self.assertEqual(st.POLICY.stat().st_mode & 0o777, 0o600)
        self.assertEqual(st.PAC_FILE.stat().st_mode & 0o777, 0o600)
        self.assertEqual(st.SERVICE.stat().st_mode & 0o777, 0o644)
        prior = st.POLICY.read_bytes()
        self.assertEqual(st.apply(st.DEFAULT_DOMAINS, 19414, "CFON")["state"], "unchanged")
        self.assertEqual(prior, st.POLICY.read_bytes())
        r = st.apply("brave.com\nstripe.com\nstripe.network\nexample.org", 19414, "CFON")
        self.assertTrue(r["ok"])
        self.assertTrue(st.status()["ok"])
        self.assertIn("example.org", st.PAC_FILE.read_text())
        self.assertNotEqual(st.pac_url(st.PAC_FILE.read_text()),
                            st.pac_url(st.pac_script(["brave.com", "bravesoftware.com",
                                "stripe.com", "stripe.network"], 19414)))
        self.assertEqual(self.setting["autoconfig-url"], st.pac_url(st.PAC_FILE.read_text()))
        off = st.disable()
        self.assertEqual(off, {"ok": True, "state": "disabled", "restored": True})
        self.assertEqual(self.setting["autoconfig-url"], "file:///owner/original.pac")
        self.assertEqual(self.setting["mode"], "auto")
        self.assertEqual(st.disable()["state"], "already-disabled")
        self.assertIn(("disable", "--now", st.SERVICE.name), self.controls)

    def test_conflict_does_not_clobber_foreign_settings(self):
        self.assertTrue(st.apply("brave.com", 19414, "CFON")["ok"])
        self.setting["autoconfig-url"] = "https://other-provider/proxy.pac"
        self.assertEqual(st.disable()["error"], "SELECTIVE_PROXY_SETTINGS_DRIFT")
        with self.assertRaises(st.SelectiveError):
            st.apply("stripe.com", 19414, "CFON")
        self.assertEqual(self.setting["autoconfig-url"], "https://other-provider/proxy.pac")
        self.setting["autoconfig-url"] = st.pac_url(st.PAC_FILE.read_text())
        self.assertTrue(st.disable()["ok"])

    def test_invalid_input_or_dead_proxy_makes_zero_settings_changes(self):
        prev = dict(self.setting)
        with self.assertRaises(ValueError):
            st.apply("stripe.com?return=DIRECT", 19414, "CFON")
        self.assertEqual(prev, self.setting)
        self.assertFalse(st.PAC_FILE.exists())
        with mock.patch.object(st, "_probe", side_effect=st.SelectiveError("DEAD_PROXY")):
            with self.assertRaises(st.SelectiveError):
                st.apply("stripe.com", 19414, "CFON")
        self.assertEqual(prev, self.setting)
        self.assertFalse(st.SERVICE.exists())

    def test_first_apply_aborts_on_foreign_owned_unit(self):
        st.SERVICE.parent.mkdir(parents=True, exist_ok=True)
        st.SERVICE.write_text("# unrelated unit, cannot be overwritten")
        with self.assertRaises(st.SelectiveError):
            st.apply("stripe.com", 19414, "CFON")
        self.assertFalse(st.PAC_FILE.exists())
        self.assertEqual(st.SERVICE.read_text(), "# unrelated unit, cannot be overwritten")
        self.assertEqual(self.setting["mode"], "auto")


if __name__ == "__main__":
    unittest.main(verbosity=2)
