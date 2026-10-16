#!/usr/bin/env python3
"""Windows selective-PAC regression without registry/network/desktop side effects."""
import copy
import pathlib
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

import http.server

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import selective_route_windows as st


class DomainTests(unittest.TestCase):
    def test_normalized_domains(self):
        self.assertEqual(
            st.normalize_domains("BRAVE.com, *.brave.com; stripe.com\nstripe.network."),
            ["brave.com", "stripe.com", "stripe.network"],
        )

    def test_rejects_unsafe_domains(self):
        bad = (
            "", "*", "co.uk", "com", "127.0.0.1", "localhost",
            "bad.local", "bad..example", "example.com:8080",
            "https://brave.com/", ";\" return DIRECT",
            "a" * 64 + ".com", "\n".join(f"n{i}.example" for i in range(65)),
        )
        for sample in bad:
            with self.subTest(domain=sample[:50]), self.assertRaises(st.SelectiveError):
                st.normalize_domains(sample)

    def test_unchanged_direct_policy_and_socks_suffixes(self):
        js = st.pac(st.normalize_domains(st.DEFAULT_DOMAINS), 19414)
        self.assertNotIn("SOCKS5 127.0.0.1:19414; DIRECT", js)
        script = (
            "const vm=require('vm');"
            "const c={dnsDomainIs:(h,s)=>h.endsWith(s)};"
            "vm.runInNewContext(process.argv[1],c);"
            "const tests=["
            "['account.brave.com','SOCKS5 127.0.0.1:19414'],"
            "['api-dashboard.search.brave.com','SOCKS5 127.0.0.1:19414'],"
            "['checkout.stripe.com','SOCKS5 127.0.0.1:19414'],"
            "['js.stripe.com','SOCKS5 127.0.0.1:19414'],"
            "['m.stripe.network','SOCKS5 127.0.0.1:19414'],"
            "['www.google.com','DIRECT'],"
            "['notbrave.com','DIRECT'],"
            "['badstripe.com','DIRECT']];"
            "for(const [host,e] of tests){"
            " const v=c.FindProxyForURL('https://'+host,host);"
            " if(v!==e){console.error(host,v,e);process.exit(2);}}"
        )
        p = subprocess.run(["node", "-e", script, js], capture_output=True, text=True, timeout=5)
        self.assertEqual(p.returncode, 0, p.stderr)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fnh-win-selective-test-")
        self.root = pathlib.Path(self.temp.name)
        self.reg = {
            "AutoConfigURL": {"present": True, "value": "https://old-owner/pac.js", "kind": 1},
            "ProxyEnable": {"present": True, "value": 0, "kind": 4},
        }
        self.before = copy.deepcopy(self.reg)
        self.patches = [
            mock.patch.object(st, "STATE", self.root / "selective"),
            mock.patch.object(st, "POLICY", self.root / "selective/policy.json"),
            mock.patch.object(st, "PAC_FILE", self.root / "selective/route.pac"),
            mock.patch.object(st, "_require_windows", return_value=None),
            mock.patch.object(st, "_snapshot", side_effect=lambda: copy.deepcopy(self.reg)),
            mock.patch.object(st, "_write_value", side_effect=self.write_reg),
            mock.patch.object(st, "_notify", return_value=None),
            mock.patch.object(st, "_check_local_socks", return_value=None),
        ]
        for p in self.patches:
            p.start()
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), st._Handler)
        self.thread = None
        self.patches += [
            mock.patch.object(st, "PORT", self.srv.server_address[1]),
            mock.patch.object(st, "URL", f"http://127.0.0.1:{self.srv.server_address[1]}/route.pac"),
            mock.patch.object(st, "_start_service", side_effect=self.start_service),
        ]
        for p in self.patches[-3:]:
            p.start()

    def write_reg(self, name, value):
        self.reg[name] = copy.deepcopy(value)

    def start_service(self, token):
        if self.thread is None:
            self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
            self.thread.start()
        self.assertTrue(st._health(token))

    def tearDown(self):
        if self.thread:
            self.srv.shutdown()
        self.srv.server_close()
        if self.thread:
            self.thread.join(timeout=3)
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def test_apply_idempotent_update_and_exact_restore(self):
        r = st.enable(st.DEFAULT_DOMAINS, 19414, "CFON")
        self.assertTrue(r["ok"])
        self.assertTrue(st.status()["healthy"])
        self.assertEqual(self.reg["AutoConfigURL"]["value"], st.pac_url(st.PAC_FILE.read_text()))
        self.assertEqual(st.enable(st.DEFAULT_DOMAINS, 19414, "CFON")["state"], "unchanged")
        version1 = self.reg["AutoConfigURL"]["value"]
        upd = st.enable("brave.com\nstripe.com\nnewsite.org", 19414, "CFON")
        self.assertEqual(upd["state"], "enabled")
        self.assertNotEqual(version1, self.reg["AutoConfigURL"]["value"])
        self.assertTrue(st.status()["ok"])
        off = st.disable()
        self.assertTrue(off["ok"] and off["restored"])
        self.assertEqual(self.reg, self.before)
        self.assertFalse(st.status()["enabled"])
        self.assertEqual(st.disable()["state"], "already-disabled")

    def test_external_mutation_not_overwritten(self):
        self.assertTrue(st.enable("brave.com", 19414, "CFON")["ok"])
        self.reg["AutoConfigURL"]["value"] = "https://another-vpn/pac"
        self.assertEqual(st.disable()["error"], "SELECTIVE_WINDOWS_PROXY_DRIFT")
        with self.assertRaises(st.SelectiveError):
            st.enable("stripe.com", 19414, "CFON")
        self.assertEqual(self.reg["AutoConfigURL"]["value"], "https://another-vpn/pac")
        self.reg["AutoConfigURL"]["value"] = st._load_state()["pacUrl"]
        self.assertTrue(st.disable()["ok"])

    def test_invalid_or_failed_proxy_never_changes_user_registry(self):
        with self.assertRaises(st.SelectiveError):
            st.enable("api.bad/evil", 19414, "CFON")
        with self.assertRaises(st.SelectiveError):
            st.enable("brave.com", 19414, "DIRECT")
        self.assertEqual(self.reg, self.before)
        with mock.patch.object(st, "_check_local_socks", side_effect=st.SelectiveError("NO_PROXY")):
            with self.assertRaises(st.SelectiveError):
                st.enable("brave.com", 19414, "CFON")
        self.assertEqual(self.reg, self.before)
        self.assertFalse(st.PAC_FILE.exists())

    def test_apply_failure_rolls_back_baseline(self):
        calls = []
        def notify_once():
            calls.append(1)
            if len(calls) == 1:
                raise st.SelectiveError("SIMULATED_NOTIFY_FAIL")
        with mock.patch.object(st, "_notify", side_effect=notify_once):
            with self.assertRaises(st.SelectiveError):
                st.enable("brave.com", 19414, "CFON")
        self.assertEqual(self.reg, self.before)
        self.assertFalse(st._load_state().get("enabled"))

    def test_interrupted_commit_state_recovers_without_touching_foreign_proxy(self):
        prior = copy.deepcopy(self.before)
        source = st.pac(["brave.com"], 19414)
        token = "ownertoken-test"
        st._atomic(st.PAC_FILE, source)
        st._write_state({
            "schema": 1, "enabled": False, "inFlight": True,
            "serverToken": token, "pacUrl": st.pac_url(source),
            "previous": prior,
        })
        self.assertFalse(st.status()["ok"])
        with self.assertRaises(st.SelectiveError):
            st.enable("brave.com", 19414, "CFON")
        # The candidate had not touched Windows settings before the crash.
        self.assertEqual(st.disable()["state"], "disabled")
        self.assertEqual(self.reg, prior)
        self.assertFalse(st._load_state()["inFlight"])

    def test_orphan_url_requires_recovery_not_adoption(self):
        self.reg["AutoConfigURL"] = {"present": True, "value": st.URL + "?v=unowned", "kind": 1}
        with self.assertRaises(st.SelectiveError):
            st.enable("brave.com", 19414, "CFON")
        self.assertFalse(st.POLICY.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
