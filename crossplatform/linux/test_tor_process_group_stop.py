#!/usr/bin/env python3
"""Mock-only regression: Tor's isolated process group must not orphan a PT.

The tested launcher creates a new session for its Tor child. Every group
signal in these tests is mocked; no owner process is started or terminated.
"""
from __future__ import annotations

import importlib.util
import pathlib
import signal
import unittest
from unittest import mock

p = pathlib.Path(__file__).with_name("freenet_hub_linux.py")
spec = importlib.util.spec_from_file_location("fnh_v594_group", p)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

PID = 54321
PT = 54322
OWNER = {"pid": PID, "exe": "/mock/tor", "start": "42"}
REUSED = {"pid": PID, "exe": "/mock/other", "start": "900"}


class TorOwnedGroupShutdownTests(unittest.TestCase):
    def simulate(self, *, term_works=True, kill_works=True, group=PID,
                 session=PID, identities=None, available=True, members=None):
        state = {"live": list(members if members is not None else [PID, PT]),
                 "signals": [], "individual_signals": []}

        def signal_group(pgid, sig):
            self.assertEqual(pgid, PID)
            state["signals"].append(sig)
            if (sig == signal.SIGTERM and term_works) or (
                sig == signal.SIGKILL and kill_works
            ):
                state["live"] = []

        def signal_pid(pid, sig):
            state["individual_signals"].append((pid, sig))

        def live_members(pgid):
            self.assertEqual(pgid, PID)
            return list(state["live"]) if available else None

        if identities is None:
            identities = [OWNER]
        identity_values = iter(identities)

        def get_identity(pid):
            self.assertEqual(pid, PID)
            return next(identity_values, identities[-1])

        with (
            mock.patch.object(m, "identity", side_effect=get_identity),
            mock.patch.object(m.os, "getpgid", return_value=group),
            mock.patch.object(m.os, "getsid", return_value=session),
            mock.patch.object(m, "_live_group_members", side_effect=live_members, create=True),
            mock.patch.object(m.os, "killpg", side_effect=signal_group, create=True),
            mock.patch.object(m.os, "kill", side_effect=signal_pid),
            mock.patch.object(m.time, "sleep"),
        ):
            result = m.stop_pid(PID)
        return result, state

    def test_stop_signals_tor_and_pluggable_transport_group(self):
        result, state = self.simulate()
        self.assertTrue(result)
        self.assertEqual(state["signals"], [signal.SIGTERM])
        self.assertFalse(state["individual_signals"])

    def test_escalation_kills_stubborn_group_members(self):
        result, state = self.simulate(term_works=False)
        self.assertTrue(result)
        self.assertEqual(state["signals"], [signal.SIGTERM, signal.SIGKILL])
        self.assertFalse(state["individual_signals"])

    def test_surviving_pt_fails_closed(self):
        result, state = self.simulate(term_works=False, kill_works=False)
        self.assertFalse(result)
        self.assertEqual(state["live"], [PID, PT])

    def test_foreign_process_group_is_not_signaled(self):
        result, state = self.simulate(group=80000)
        self.assertFalse(result)
        self.assertFalse(state["signals"])
        self.assertFalse(state["individual_signals"])

    def test_foreign_session_is_not_signaled(self):
        result, state = self.simulate(session=80000)
        self.assertFalse(result)
        self.assertFalse(state["signals"])

    def test_identity_replacement_is_not_signaled(self):
        result, state = self.simulate(identities=[OWNER, REUSED])
        self.assertFalse(result)
        self.assertFalse(state["signals"])

    def test_unidentified_leader_is_not_signaled(self):
        result, state = self.simulate(identities=[None])
        self.assertFalse(result)
        self.assertFalse(state["signals"])

    def test_unreadable_membership_fails_closed(self):
        result, state = self.simulate(available=False)
        self.assertFalse(result)
        self.assertFalse(state["signals"])

    def test_missing_group_leader_fails_closed(self):
        result, state = self.simulate(members=[PT])
        self.assertFalse(result)
        self.assertFalse(state["signals"])


if __name__ == "__main__":
    unittest.main()
