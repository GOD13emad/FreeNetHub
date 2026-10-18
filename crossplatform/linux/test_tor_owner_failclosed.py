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
