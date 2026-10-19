#!/usr/bin/env python3
"""Read-only, no-network regression for real Tor launcher ownership gates.

Every external process/ss/identity/time call is replaced by an in-memory mock.
No Tor process is started. No real user state, routes or proxy are modified.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile
from contextlib import ExitStack
from unittest import mock


SOURCE = pathlib.Path(__file__).with_name("freenet_hub_linux.py")
spec = importlib.util.spec_from_file_location("fnh_v587_tor_guard", SOURCE)
assert spec is not None and spec.loader is not None
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class FakeTor:
    pid = 54321

    def poll(self):
        return None


class FastClock:
    def __init__(self):
        self.now = 100.0

    def time(self):
        value = self.now
        self.now += 1
        return value

    def sleep(self, _seconds):
        self.now += 1


def run_case(*, identity, listener, startup=100, atomic_error=False,
             last_mode_error=False, foreign_listener=False, stop_fail=False):
    with tempfile.TemporaryDirectory(prefix="fnh-tor-identity-regression-") as tmp:
        root = pathlib.Path(tmp)
        tor_dir = root / "tor"
        tor_dir.mkdir()
        owner = tor_dir / "owner.json"
        last = tor_dir / "last_mode.txt"
        stopped = []
        spawned = []
        clock = FastClock()
        fake = FakeTor()

        def popen(*args, **kwargs):
            assert args[0][0] == "/mock/tor"
            assert args[0][1] == "-f"
            assert kwargs.get("start_new_session")
            spawned.append(args[0])
            return fake

        def atomic_json(path, value):
            if atomic_error:
                raise OSError("MOCK_PERMISSION_DENIED")
            path.write_text(json.dumps(value), encoding="utf-8")

        def stop_pid(pid):
            stopped.append(pid)
            return not stop_fail

        class ModeWriteFails:
            def write_text(self, *_args, **_kwargs):
                raise OSError("MOCK_MODE_WRITE_FAILURE")

        with ExitStack() as stack:
            patches = {
                "TOR_STATE": tor_dir,
                "TOR_OWNER": owner,
                "TOR_LAST_MODE": ModeWriteFails() if last_mode_error else last,
                "executable": lambda name: "/mock/tor" if name == "tor" else None,
                "recover_stale_project_listener":
                    (lambda: {"ok": False, "error": "MOCK_FOREIGN_PROCESS"})
                    if foreign_listener else
                    (lambda: {"ok": True, "state": "free"}),
                "identity": lambda _pid: identity,
                "listener_pid": lambda _port: listener,
                "bootstrap_percent": lambda _path: startup,
                "atomic_json": atomic_json,
                "stop_pid": stop_pid,
                "ensure_dirs": lambda: None,
                "time": clock,
            }
            for name, obj in patches.items():
                stack.enter_context(mock.patch.object(m, name, obj))
            stack.enter_context(mock.patch.object(m.subprocess, "Popen", popen))
            result = m.launch_tor("direct", 5)
        stored = json.loads(owner.read_text()) if owner.exists() else None
        return result, stopped, stored, last.read_text() if last.exists() else None, spawned


owned = {"pid": FakeTor.pid, "exe": "/mock/tor", "start": "300000"}
result, stops, record, mode, proc = run_case(identity=None, listener=FakeTor.pid)
assert not result["ok"] and result["error"] == "TOR_CHILD_IDENTITY_UNVERIFIED"
assert result["cleanupVerified"] and stops == [FakeTor.pid]
assert record is None and mode is None and len(proc) == 1
print("PASS_NO_OWNER_IDENTITY_STOPS_EXACT_CHILD")

result, stops, record, mode, proc = run_case(identity=owned, listener=None)
assert not result["ok"] and result["error"] == "TOR_SOCKS_LISTENER_OWNER_UNVERIFIED"
assert result["cleanupVerified"] and stops == [FakeTor.pid]
assert record is None and mode is None
print("PASS_MISSING_SOCKS_LISTENER_STOPS_EXACT_CHILD")

result, stops, record, mode, proc = run_case(identity=owned, listener=87432)
assert not result["ok"] and result["error"] == "TOR_SOCKS_LISTENER_OWNER_UNVERIFIED"
assert result["cleanupVerified"] and stops == [FakeTor.pid]
assert record is None and mode is None
print("PASS_FOREIGN_SOCKS_LISTENER_STOPS_EXACT_CHILD")

result, stops, record, mode, proc = run_case(identity=owned, listener=FakeTor.pid)
assert result["ok"] and result["bootstrap"] == 100
assert stops == [] and record["pid"] == FakeTor.pid and mode == "direct"
print("PASS_VERIFIED_CHILD_AND_LISTENER_ALLOW_OWNER_RECORD")

result, stops, record, mode, proc = run_case(identity=owned, listener=FakeTor.pid, atomic_error=True)
assert not result["ok"] and result["error"] == "TOR_OWNER_RECORD_PERSIST_FAILED"
assert result["cleanupVerified"] and stops == [FakeTor.pid] and record is None and mode is None
print("PASS_OWNER_WRITE_FAILURE_STOPS_EXACT_CHILD")

result, stops, record, mode, proc = run_case(identity=owned, listener=FakeTor.pid, last_mode_error=True)
assert not result["ok"] and result["error"] == "TOR_OWNER_RECORD_PERSIST_FAILED"
assert result["cleanupVerified"] and stops == [FakeTor.pid] and record is None
print("PASS_LAST_MODE_WRITE_FAILURE_REMOVES_ONLY_SCOPED_OWNER")

# If the scoped stop operation fails, keep the exact owner record rather than
# deleting recoverability metadata for a still-running owned Tor process.
result, stops, record, mode, proc = run_case(
    identity=owned, listener=FakeTor.pid, last_mode_error=True, stop_fail=True,
)
assert not result["ok"] and result["cleanupVerified"] is False
assert stops == [FakeTor.pid] and record["pid"] == FakeTor.pid
print("PASS_FAILED_STOP_PRESERVES_SCOPED_OWNER_RECORD")

result, stops, record, mode, proc = run_case(identity=owned, listener=FakeTor.pid, startup=50)
assert not result["ok"] and result["error"] == "bootstrap timeout" and result["bootstrap"] == 50
assert stops == [FakeTor.pid] and record is None and mode is None
print("PASS_BOOTSTRAP_50_PERCENT_FAILS_CLOSED")

result, stops, record, mode, proc = run_case(identity=owned, listener=FakeTor.pid, foreign_listener=True)
assert not result["ok"] and result["error"] == "MOCK_FOREIGN_PROCESS"
assert stops == [] and record is None and mode is None and not proc
print("PASS_FOREIGN_PREEXISTING_LISTENER_REFUSED_BEFORE_START")

print("V587_TOR_OWNER_IDENTIFICATION_AND_BOOTSTRAP_FAILCLOSED_9_CASES_PASS")


# V590: a passing Tor bootstrap followed by failed *egress* must not erase
# ownership metadata if the actual Tor child cannot be stopped.
def run_egress_cleanup(*, stop_ok, reassign_owner=False, owner_after_spawn=True):
    with tempfile.TemporaryDirectory(prefix="fnh-tor-egress-owner-") as tmp:
        owner_file = pathlib.Path(tmp) / "owner.json"
        old = dict(owned)
        old.update(mode="direct")
        if owner_after_spawn:
            owner_file.write_text(json.dumps(old), encoding="utf-8")
        stops = []
        other = {**old, "pid": 77777}
        if reassign_owner:
            owner_file.write_text(json.dumps(other), encoding="utf-8")

        def stop(pid):
            stops.append(pid)
            return stop_ok

        with (mock.patch.object(m, "TOR_OWNER", owner_file),
              mock.patch.object(m, "tor_owner", side_effect=[None, old if owner_after_spawn else None]),
              mock.patch.object(m, "launch_tor", return_value={
                  "ok": True, "mode": "direct", "proxy": "socks5h://127.0.0.1:9909",
              }) as launch,
              mock.patch.object(m, "trace", return_value={
                  "ok": False, "error": "MOCK_UNREACHABLE_EGRESS",
              }),
              mock.patch.object(m, "stop_pid", side_effect=stop),
              mock.patch.object(m, "set_session") as session_write):
            result = m.start_tor("direct")
        state = json.loads(owner_file.read_text()) if owner_file.exists() else None
        session_write.assert_not_called()
        launch.assert_called_once()
        return result, stops, state


result, stops, state = run_egress_cleanup(stop_ok=False)
assert not result["ok"] and result["error"] == "TOR_EGRESS_STOP_UNVERIFIED"
assert result["cleanupVerified"] is False
assert stops == [FakeTor.pid] and state["pid"] == FakeTor.pid
print("PASS_V590_FAILED_EGRESS_STOP_PRESERVES_OWNER")

result, stops, state = run_egress_cleanup(stop_ok=True)
assert not result["ok"] and result["state"] == "failed"
assert stops == [FakeTor.pid] and state is None
print("PASS_V590_SUCCESSFUL_STOP_REMOVES_EXACT_OWNER")

result, stops, state = run_egress_cleanup(stop_ok=True, reassign_owner=True)
assert not result["ok"] and stops == [FakeTor.pid]
assert state is not None and state["pid"] == 77777
print("PASS_V590_OWNER_RACE_DOES_NOT_UNLINK_FOREIGN_RECORD")

result, stops, state = run_egress_cleanup(stop_ok=True, owner_after_spawn=False)
assert not result["ok"] and result["error"] == "TOR_EGRESS_OWNER_UNVERIFIED"
assert result["cleanupVerified"] is False and stops == [] and state is None
print("PASS_V590_MISSING_EGRESS_OWNER_FAILS_CLOSED")

with (mock.patch.object(m, "tor_owner", return_value=owned),
      mock.patch.object(m, "trace", return_value={"ok": False}),
      mock.patch.object(m, "stop_tor", return_value={"ok": False, "state": "stop-timeout"}),
      mock.patch.object(m, "launch_tor") as new_tor):
    result = m.start_tor("direct")
assert not result["ok"] and result["error"] == "TOR_PREVIOUS_OWNER_STOP_UNVERIFIED"
assert result["cleanupVerified"] is False
new_tor.assert_not_called()
print("PASS_V590_PREEXISTING_UNSTOPPABLE_TOR_BLOCKS_NEW_START")

print("V590_TOR_EGRESS_OWNERSHIP_RECOVERY_5_CASES_PASS")


# V593: Recovery must never remove an owner record just because a known
# localhost listener was identified; a failed stop can leave it running.
def run_stale_listener_record_case(stop_succeeds):
    with tempfile.TemporaryDirectory(prefix="fnh-stale-owner-protection-") as tmp:
        state = pathlib.Path(tmp) / "tor"
        state.mkdir()
        owner_file = state / "owner.json"
        sentinel = {"pid": 76543, "exe": "/mock/tor", "start": "777"}
        owner_file.write_text(json.dumps(sentinel), encoding="utf-8")
        pid = 54321
        real_read = pathlib.Path.read_bytes

        def mocked_read_bytes(path):
            if str(path) == f"/proc/{pid}/cmdline":
                return f"/mock/tor\\0-f\\0{state}/torrc-obfs4\\0".replace(
                    "\\0", "\0").encode()
            return real_read(path)

        with (mock.patch.object(m, "TOR_STATE", state),
              mock.patch.object(m, "TOR_OWNER", owner_file),
              mock.patch.object(m, "listener_pid", return_value=pid),
              mock.patch.object(m, "tor_owner", return_value=None),
              mock.patch.object(m, "identity", return_value={
                  "pid": pid, "exe": "/mock/tor", "start": "321"}),
              mock.patch.object(m, "executable", return_value="/mock/tor"),
              mock.patch.object(pathlib.Path, "read_bytes", mocked_read_bytes),
              mock.patch.object(m, "stop_pid", return_value=stop_succeeds)):
            outcome = m.recover_stale_project_listener()
        surviving = json.loads(owner_file.read_text()) if owner_file.exists() else None
        return outcome, surviving, sentinel


outcome, kept, original = run_stale_listener_record_case(False)
assert not outcome["ok"] and kept == original
print("PASS_V593_FAILED_STALE_RECOVERY_PRESERVES_OTHER_OWNER")

outcome, kept, original = run_stale_listener_record_case(True)
assert outcome["ok"] and kept == original
print("PASS_V593_SUCCESSFUL_STALE_RECOVERY_DOES_NOT_ERASE_OTHER_OWNER")


def run_stop_tor_race_case(stop_succeeds=True, owner_changed=False):
    with tempfile.TemporaryDirectory(prefix="fnh-stop-owner-race-") as tmp:
        owner_file = pathlib.Path(tmp) / "owner.json"
        original = dict(owned, mode="obfs4")
        foreign = dict(original, pid=original["pid"] + 100)
        owner_file.write_text(json.dumps(original), encoding="utf-8")

        def stop(pid):
            assert pid == owned["pid"]
            if owner_changed:
                owner_file.write_text(json.dumps(foreign), encoding="utf-8")
            return stop_succeeds

        with (mock.patch.object(m, "TOR_OWNER", owner_file),
              mock.patch.object(m, "tor_owner", return_value=original),
              mock.patch.object(m, "stop_pid", side_effect=stop),
              mock.patch.object(m, "session", return_value={"mode": "TOR"}),
              mock.patch.object(m, "set_session") as clear_session):
            result = m.stop_tor()
        contents = json.loads(owner_file.read_text()) if owner_file.exists() else None
        return result, contents, clear_session.call_count, original, foreign


result, record, calls, _original, foreign = run_stop_tor_race_case(owner_changed=True)
assert not result["ok"] and result["state"] == "owner-record-changed"
assert record == foreign and calls == 0
print("PASS_V593_STOP_RACE_DOES_NOT_DELETE_FOREIGN_OWNER")

result, record, calls, original, _foreign = run_stop_tor_race_case(stop_succeeds=False)
assert not result["ok"] and result["state"] == "stop-timeout"
assert record == original and calls == 0
print("PASS_V593_UNSTOPPABLE_OWNER_KEEPS_RECORD_AND_SESSION")

result, record, calls, _original, _foreign = run_stop_tor_race_case()
assert result["ok"] and result["state"] == "stopped"
assert record is None and calls == 1
print("PASS_V593_EXACT_OWNER_STOP_CLEARS_ONLY_MATCHING_RECORD")

# Full Stop must not clear session when its own Tor stop has not succeeded.
with (mock.patch.object(m, "session", return_value={"mode": "TOR"}),
      mock.patch.object(m, "stop_tor", return_value={"ok": False, "state": "stop-timeout"}),
      mock.patch.object(m, "warp_status", return_value={"connected": False}),
      mock.patch.object(m, "set_session") as reset_session):
    result = m.stop_all()
assert not result["ok"]
reset_session.assert_not_called()
print("PASS_V593_STOP_ALL_FAILCLOSED_SESSION")

result, stops, record, mode, proc = run_case(
    identity=owned, listener=FakeTor.pid, startup=50, stop_fail=True,
)
assert not result["ok"] and result["error"] == "bootstrap timeout"
assert result.get("cleanupVerified") is False and stops == [FakeTor.pid]
print("PASS_V593_BOOTSTRAP_FAILED_STOP_EXPLICITLY_UNVERIFIED")

print("V593_LINUX_TOR_OWNER_RECOVERY_SAFETY_7_CASES_PASS")
