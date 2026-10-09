"""Protected site reachability and smart CFON fallback regression, no host routing."""
import pathlib
import sys
from unittest import mock

LINUX = pathlib.Path(__file__).resolve().parents[1] / "crossplatform" / "linux"
sys.path.insert(0, str(LINUX))
import freenet_hub_linux_r37 as core


def test_requires_owned_proxy_and_never_tests_direct():
    with mock.patch.object(core.legacy, "session", return_value={"mode": None}), \
         mock.patch.object(core.legacy, "run") as run:
        r = core.test_active_sites()
    assert not r["ok"] and r["error"] == "CONNECT_PROTECTED_BROWSER_FIRST"
    run.assert_not_called()


def test_disconnected_cfon_never_falls_back_to_unprotected_internet():
    with mock.patch.object(core.legacy, "session", return_value={"mode": "CFON"}), \
         mock.patch.object(core, "_warpplus_owner", return_value=None), \
         mock.patch.object(core.legacy, "run") as run:
        r = core.test_active_sites()
    assert not r["ok"] and r["error"] == "CONNECT_PROTECTED_BROWSER_FIRST"
    run.assert_not_called()


def test_site_diagnostics_uses_socks_and_explicit_destination():
    samples = [(204, 0), (200, 0), (200, 0), (403, 0)]
    calls = []

    def fake_run(argv, timeout):
        calls.append(argv)
        n = len(calls) - 1
        assert argv[-1] == core.ACTIVE_SITE_TARGETS[n][1]
        assert "--proxy" in argv
        assert argv[argv.index("--proxy") + 1] == "socks5h://127.0.0.1:19414"
        return mock.Mock(stdout=str(samples[n][0]), returncode=samples[n][1])

    with mock.patch.object(core, "_active_proxy_for_diagnostics", return_value=("socks5h://127.0.0.1:19414", "CFON")), \
         mock.patch.object(core.legacy, "executable", return_value="/usr/bin/curl"), \
         mock.patch.object(core.legacy, "run", side_effect=fake_run):
        r = core.test_active_sites()
    assert r["ok"] and r["scope"] == "BROWSER" and len(calls) == 4
    assert r["passed"] == 3
    assert r["results"][-1]["status"] == "HTTP_RESTRICTED_OR_CHALLENGED"


def test_no_target_url_or_failed_transports_are_accepted():
    with mock.patch.object(core, "_active_proxy_for_diagnostics", return_value=("socks5h://127.0.0.1:19414", "CFON")), \
         mock.patch.object(core.legacy, "run", return_value=mock.Mock(stdout="000", returncode=2)):
        r = core.test_active_sites()
    assert not r["ok"] and r["passed"] == 0
    assert all(not item["transportOK"] for item in r["results"])


def test_auto_tries_cfon_before_warp_and_accepts_sites():
    calls = []
    def start(mode):
        calls.append(mode)
        return {"ok": True, "country": "AT"}

    with mock.patch.object(core, "singbox_status", return_value={"ok": False}), \
         mock.patch.object(core, "warpplus_status", return_value={"ok": True}), \
         mock.patch.object(core, "warpplus_start", side_effect=start), \
         mock.patch.object(core, "test_active_sites", return_value={"ok": True, "passed": 3}) as sites, \
         mock.patch.object(core, "_warpplus_stop") as stop, \
         mock.patch.object(core.legacy, "start_tor") as tor:
        r = core.connect_method("AUTO", "BROWSER")
    assert r["selected"] == "CFON" and calls == ["CFON"]
    sites.assert_called_once()
    stop.assert_not_called()
    tor.assert_not_called()


def test_auto_rejects_cfon_without_real_targets_then_fallback_warp():
    calls = []
    def start(mode):
        calls.append(mode)
        return {"ok": True}

    with mock.patch.object(core, "singbox_status", return_value={"ok": False}), \
         mock.patch.object(core, "warpplus_status", return_value={"ok": True}), \
         mock.patch.object(core, "warpplus_start", side_effect=start), \
         mock.patch.object(core, "test_active_sites", return_value={"ok": False}), \
         mock.patch.object(core, "_warpplus_stop", return_value={"ok": True}) as stop:
        r = core.connect_method("AUTO", "BROWSER")
    assert r["selected"] == "WARP" and calls == ["CFON", "WARP"]
    stop.assert_called_once_with("CFON")


def test_system_cfon_remains_explicitly_blocked():
    with mock.patch.object(core.legacy, "connect_mode") as legacy:
        r = core.connect_method("CFON", "SYSTEM")
    assert not r["ok"] and r["error"] == "LINUX_FULL_SYSTEM_WARP_ONLY"
    legacy.assert_not_called()


def test_no_arbitrary_site_target_injection():
    with mock.patch.object(core, "_active_proxy_for_diagnostics", return_value=("socks5h://127.0.0.1:19414", "CFON")):
        try:
            core.test_active_sites(targets=(("untrusted", "https://evil.invalid"),))
        except ValueError as exc:
            assert str(exc) == "SITE_TEST_TARGET_NOT_ALLOWLISTED"
        else:
            raise AssertionError("UNTRUSTED_SITE_ACCEPTED")


if __name__ == "__main__":
    for name,fn in sorted(globals().copy().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(name, "PASS")
