"""Regression: browser actions must be explicit, fail closed and report launch failures."""
import pathlib
import sys
from unittest import mock

LINUX = pathlib.Path(__file__).resolve().parents[1] / "crossplatform" / "linux"
sys.path.insert(0, str(LINUX))
import freenet_hub_linux_r37 as core


def test_tunneled_browser_requires_connection():
    with mock.patch.object(core.legacy, "session", return_value={"mode": None}), \
         mock.patch.object(core.legacy, "executable", return_value="/usr/bin/firefox"), \
         mock.patch.object(core.subprocess, "Popen") as popen:
        result = core.open_browser("about:blank")
    assert not result["ok"] and result["error"] == "CONNECT_FIRST"
    popen.assert_not_called()


def test_tunneled_browser_reports_failed_launch(tmp_path):
    proc = mock.Mock()
    proc.poll.return_value = 1
    with mock.patch.object(core.legacy, "session", return_value={"mode": "DIRECT"}), \
         mock.patch.object(core.legacy, "executable", return_value="/usr/bin/firefox"), \
         mock.patch.object(core.legacy, "stop_project_firefox", return_value={"ok": True}), \
         mock.patch.object(core.legacy, "project_firefox_pids", return_value=[]), \
         mock.patch.object(core, "_firefox_profile", return_value=tmp_path), \
         mock.patch.object(core.subprocess, "Popen", return_value=proc), \
         mock.patch.object(core.time, "sleep"):
        result = core.open_browser("about:blank")
    assert not result["ok"] and result["error"] == "BROWSER_LAUNCH_FAILED"


def test_tunneled_browser_only_passes_on_live_pid(tmp_path):
    proc = mock.Mock()
    proc.poll.return_value = None
    with mock.patch.object(core.legacy, "session", return_value={"mode": "DIRECT"}), \
         mock.patch.object(core.legacy, "executable", return_value="/usr/bin/firefox"), \
         mock.patch.object(core.legacy, "stop_project_firefox", return_value={"ok": True}), \
         mock.patch.object(core.legacy, "project_firefox_pids", return_value=[1234]), \
         mock.patch.object(core, "_firefox_profile", return_value=tmp_path), \
         mock.patch.object(core.subprocess, "Popen", return_value=proc), \
         mock.patch.object(core.time, "sleep"):
        result = core.open_browser("about:blank")
    assert result["ok"] and result["pids"] == [1234]


def test_direct_browser_is_explicit_and_never_creates_tunnel():
    proc = mock.Mock()
    proc.poll.return_value = 0
    with mock.patch.object(core.legacy, "executable", return_value="/usr/bin/xdg-open"), \
         mock.patch.object(core.subprocess, "Popen", return_value=proc) as popen, \
         mock.patch.object(core.time, "sleep"):
        result = core.open_direct_browser("about:blank")
    assert result["ok"] and result["mode"] == "DIRECT_UNPROTECTED"
    assert result["state"] == "DISPATCHED_NOT_WINDOW_VERIFIED"
    assert popen.call_args.args[0] == ["/usr/bin/xdg-open", "about:blank"]
