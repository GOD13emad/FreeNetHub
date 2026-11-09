#!/usr/bin/env python3
"""No-network regression for the Linux explicit DIRECT versus SOCKS test paths.

An ambient NO_PROXY=* must never turn a tunneled test into a DIRECT probe,
and proxy environment variables must not silently alter a base-route test.
All subprocesses are mocked, and upload samples live in a disposable temp dir.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import freenet_hub_linux as legacy
import freenet_hub_linux_r37 as r37

SOCKS = "socks5h://127.0.0.1:19979"
ENV = {
    "NO_PROXY": "*", "no_proxy": "*",
    "HTTP_PROXY": "http://127.0.0.1:19978",
    "HTTPS_PROXY": "http://127.0.0.1:19978",
    "ALL_PROXY": "socks5://127.0.0.1:19978",
}
URL = "https://www.cloudflare.com/cdn-cgi/trace"


class CurlPathTests(unittest.TestCase):
    def assert_path(self, args, tunneled):
        self.assertEqual(args.count("--noproxy"), 1, args)
        bypass = args[args.index("--noproxy") + 1]
        self.assertEqual(bypass, "" if tunneled else "*")
        self.assertEqual(args.count("--proxy"), 1 if tunneled else 0, args)
        if tunneled:
            self.assertEqual(args[args.index("--proxy") + 1], SOCKS)

    def test_legacy_trace_tor_uses_socks_not_no_proxy_direct(self):
        requests = []

        def fake_run(args, timeout):
            requests.append(list(args))
            return subprocess.CompletedProcess(args, 0, "ip=203.0.113.17\nloc=NL\n", "")

        with (mock.patch.dict(os.environ, ENV),
              mock.patch.object(legacy, "executable", return_value="curl"),
              mock.patch.object(legacy, "run", side_effect=fake_run)):
            result = legacy.trace(proxy=SOCKS, timeout=5)
        self.assertTrue(result["ok"])
        self.assertEqual(result["trace"]["loc"], "NL")
        self.assertEqual(len(requests), 1)
        self.assert_path(requests[0], tunneled=True)
        self.assertEqual(requests[0][-1], URL)

    def test_legacy_trace_direct_ignores_external_proxy_env(self):
        requests = []

        def fake_run(args, timeout):
            requests.append(list(args))
            return subprocess.CompletedProcess(args, 0, "ip=203.0.113.17\n", "")

        with (mock.patch.dict(os.environ, ENV),
              mock.patch.object(legacy, "executable", return_value="curl"),
              mock.patch.object(legacy, "run", side_effect=fake_run)):
            result = legacy.trace(timeout=5)
        self.assertTrue(result["ok"])
        self.assertEqual(len(requests), 1)
        self.assert_path(requests[0], tunneled=False)

    def test_r37_ping_download_tunnel_and_direct_are_explicit(self):
        requests = []

        def fake_run(args, timeout):
            requests.append(list(args))
            out = "\n__FNH__200\t0.12\t10000\t0\t92"
            return subprocess.CompletedProcess(args, 0, out, "")

        with (mock.patch.dict(os.environ, ENV),
              mock.patch.object(legacy, "executable", return_value="curl"),
              mock.patch.object(legacy, "run", side_effect=fake_run)):
            proxy = r37._curl(URL, timeout=4, proxy=SOCKS, body=False)
            direct = r37._curl(URL, timeout=4, proxy=None, body=False, interface="enp7s0")
        self.assertEqual(proxy["code"], "200")
        self.assertEqual(direct["code"], "200")
        self.assertEqual(len(requests), 2)
        self.assert_path(requests[0], tunneled=True)
        self.assert_path(requests[1], tunneled=False)
        self.assertEqual(requests[1][requests[1].index("--interface") + 1], "enp7s0")

    def test_r37_speed_upload_tunnel_and_direct_are_explicit(self):
        requests = []
        original_temp = tempfile.mkstemp

        with tempfile.TemporaryDirectory(prefix="fnh-v590-upload-mock-") as tmp:
            def sandbox_temp(*args, **kwargs):
                return original_temp(prefix="fnh-test-upload-", suffix=".bin", dir=tmp)

            def fake_run(args, timeout):
                requests.append(list(args))
                return subprocess.CompletedProcess(args, 0, "200\t0.25\t500.0", "")

            with (mock.patch.dict(os.environ, ENV),
                  mock.patch.object(legacy, "executable", return_value="curl"),
                  mock.patch.object(legacy, "run", side_effect=fake_run),
                  mock.patch.object(r37.tempfile, "mkstemp", side_effect=sandbox_temp)):
                via = r37._upload(proxy=SOCKS, timeout=3, bytes_count=64)
                base = r37._upload(proxy=None, timeout=3, bytes_count=64)
            self.assertEqual(via["code"], "200")
            self.assertEqual(base["code"], "200")
            self.assertEqual(list(pathlib.Path(tmp).iterdir()), [])
        self.assertEqual(len(requests), 2)
        self.assert_path(requests[0], tunneled=True)
        self.assert_path(requests[1], tunneled=False)

    def test_allowlisted_google_selected_site_diagnostics_force_socks(self):
        requests = []
        google = next((label, url) for label, url in r37.ACTIVE_SITE_TARGETS if label == "Google")

        def fake_run(args, timeout):
            requests.append(list(args))
            return subprocess.CompletedProcess(args, 0, "200", "")

        with (mock.patch.dict(os.environ, ENV),
              mock.patch.object(r37, "_active_proxy_for_diagnostics", return_value=(SOCKS, "NODE")),
              mock.patch.object(legacy, "executable", return_value="curl"),
              mock.patch.object(legacy, "run", side_effect=fake_run)):
            result = r37.test_active_sites(targets=(google,), timeout=5)
        self.assertEqual(result["results"][0]["code"], "200")
        self.assertEqual(len(requests), 1)
        self.assert_path(requests[0], tunneled=True)
        self.assertEqual(requests[0][-1], google[1])

    def test_legacy_speed_sample_tunnel_and_direct_are_explicit(self):
        requests = []

        def fake_run(args, timeout):
            requests.append(list(args))
            return subprocess.CompletedProcess(args, 0, "15000.0", "")

        with (mock.patch.dict(os.environ, ENV),
              mock.patch.object(legacy, "executable", return_value="curl"),
              mock.patch.object(legacy, "session", return_value={"mode": "TOR"}),
              mock.patch.object(legacy, "run", side_effect=fake_run)):
            with mock.patch.object(legacy, "browser_proxy_port", return_value=19979):
                self.assertTrue(legacy.speed_sample()["ok"])
            with mock.patch.object(legacy, "browser_proxy_port", return_value=None):
                self.assertTrue(legacy.speed_sample()["ok"])
        self.assert_path(requests[0], tunneled=True)
        self.assert_path(requests[1], tunneled=False)

    def test_direct_doctor_youtube_does_not_use_proxy_env(self):
        requests = []

        def fake_run(args, timeout):
            requests.append(list(args))
            if args[0] == "getent":
                return subprocess.CompletedProcess(args, 0, "203.0.113.17 www.google.com\n", "")
            return subprocess.CompletedProcess(args, 0, "204", "")

        with (mock.patch.dict(os.environ, ENV),
              mock.patch.object(legacy, "trace", return_value={"ok": True}),
              mock.patch.object(legacy, "executable", return_value="curl"),
              mock.patch.object(legacy, "run", side_effect=fake_run),
              mock.patch.object(legacy, "default_route", return_value={})):
            result = legacy.doctor()
        self.assertTrue(result["youtube_reachable"])
        youtube = next(x for x in requests if "www.youtube.com/generate_204" in x[-1])
        self.assert_path(youtube, tunneled=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
