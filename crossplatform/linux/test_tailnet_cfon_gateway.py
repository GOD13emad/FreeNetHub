#!/usr/bin/env python3
"""No-host-mutation tests for private Tailnet-only CFON egress (stdlib)."""
import pathlib
import socket
import subprocess
import threading
import tempfile
import json
import unittest
from unittest import mock
import sys

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import tailnet_cfon_gateway as m


def exact(sock,n):
    value=b""
    while len(value)<n:
        part=sock.recv(n-len(value))
        if not part:raise RuntimeError("SOCKS_EOF")
        value+=part
    return value


class FakeCFON:
    def __init__(self):
        self.listener=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.listener.bind(("127.0.0.1",0))
        self.listener.listen(1)
        self.port=self.listener.getsockname()[1]
        self.targets=[]
        self.error=None
        self.thread=threading.Thread(target=self.run,daemon=True)
        self.thread.start()

    def run(self):
        try:
            with self.listener.accept()[0] as c:
                c.settimeout(5)
                assert exact(c,3)==b"\x05\x01\x00"
                c.sendall(b"\x05\x00")
                assert exact(c,4)==b"\x05\x01\x00\x03"
                name=exact(c,exact(c,1)[0]).decode("ascii")
                port=int.from_bytes(exact(c,2),"big")
                self.targets.append((name,port))
                c.sendall(b"\x05\x00\x00\x01\x7f\x00\x00\x01\x00\x00")
                payload=c.recv(100)
                c.sendall(b"ACK:"+payload)
        except Exception as exc:
            self.error=str(exc)
        finally:
            self.listener.close()

    def wait(self):
        self.thread.join(timeout=5)
        assert not self.thread.is_alive()
        assert self.error is None,self.error


class PeerProof(unittest.TestCase):
    def test_tailnet_rejects_public_local_v6_or_self(self):
        for ip in ("127.0.0.1","192.168.20.6","8.8.8.8","::1","fd7a:115c::1","100.63.255.255","100.128.0.1"):
            with self.subTest(ip=ip),self.assertRaises(m.TailnetError):
                m.tailnet_ip(ip)
        self.assertEqual(m.tailnet_ip("100.100.42.2"),"100.100.42.2")
        ts={"BackendState":"Running",
            "Self":{"TailscaleIPs":["100.100.42.1"],"Online":True},
            "Peer":{"peer": {"TailscaleIPs":["100.100.42.2"],"Online":True}}}
        self.assertEqual(m.verify_peers("100.100.42.1","100.100.42.2",ts),
                         ("100.100.42.1","100.100.42.2"))
        with self.assertRaises(m.TailnetError):
            m.verify_peers("100.100.42.1","100.100.42.1",ts)
        with self.assertRaises(m.TailnetError):
            m.verify_peers("100.100.42.1","100.100.42.4",ts)
        ts["Peer"]["peer"]["Online"]=False
        with self.assertRaises(m.TailnetError):
            m.verify_peers("100.100.42.1","100.100.42.2",ts)

    def test_exact_suffix_https_and_remote_dns_only(self):
        for value in (b"console.cloud.google.com",b"google.com"):
            self.assertEqual(m._safe_host(value,["google.com"]),value.decode())
        for host in (b"notgoogle.com",b"google.com.evil.net",b"127.0.0.1",
                     b"goo\ngle.com",b"-invalid.google.com",b"foo_google.com"):
            with self.subTest(host=host),self.assertRaises(m.TailnetError):
                m._safe_host(host,["google.com"])

    def test_emits_socks5_only_for_allowed_google_cloud_dns443(self):
        fake=FakeCFON()
        with mock.patch.object(m,"UPSTREAM_PORT",fake.port):
            c,s=socket.socketpair()
            worker=threading.Thread(target=m.exchange,args=(s,["google.com"]),daemon=True)
            worker.start()
            try:
                c.settimeout(5)
                c.sendall(b"\x05\x01\x00")
                self.assertEqual(exact(c,2),b"\x05\x00")
                host=b"console.cloud.google.com"
                c.sendall(b"\x05\x01\x00\x03"+bytes([len(host)])+host+b"\x01\xbb")
                self.assertEqual(exact(c,10),b"\x05\x00\x00\x01"+b"\x00"*6)
                c.sendall(b"TEST_TLS")
                self.assertEqual(exact(c,12),b"ACK:TEST_TLS")
            finally:
                c.close()
                worker.join(timeout=5)
        fake.wait()
        self.assertEqual(fake.targets,[("console.cloud.google.com",443)])

    def test_denies_foreign_host_and_plain_http_without_upstream(self):
        for domain,port in (("notgoogle.com",443),("google.com.evil.net",443),("google.com",80)):
            with self.subTest(domain=domain,port=port):
                c,s=socket.socketpair()
                worker=threading.Thread(target=m.exchange,args=(s,["google.com"]),daemon=True)
                worker.start()
                try:
                    c.settimeout(3)
                    c.sendall(b"\x05\x01\x00")
                    self.assertEqual(exact(c,2),b"\x05\x00")
                    host=domain.encode("ascii")
                    c.sendall(b"\x05\x01\x00\x03"+bytes([len(host)])+host+port.to_bytes(2,"big"))
                    self.assertEqual(exact(c,2)[0],5)   # non-success response
                finally:
                    c.close()
                    worker.join(timeout=3)

    def test_owned_optin_start_and_stop_never_stop_cfon_or_autostart(self):
        with tempfile.TemporaryDirectory(prefix="fnh-tailnet-test-") as root:
            base=pathlib.Path(root)
            owner=base/"state"/"tailnet_cfon_gateway.json"
            unit=base/"user"/"freenethub-tailnet-cfon.service"
            sample={"BackendState":"Running",
                "Self":{"TailscaleIPs":["100.100.42.1"],"Online":True},
                "Peer":{"peer":{"OS":"windows","HostName":"WindowsDemo",
                                "TailscaleIPs":["100.100.42.2"],"Online":True}}}
            mocked_status=[{"ok":True,"enabled":False,"active":False},
                            {"ok":True,"enabled":True,"active":True}]
            recorded=[]
            def command(argv,**kw):
                recorded.append(tuple(argv))
                return subprocess.CompletedProcess(argv,0,"","")
            with mock.patch.object(m,"OWNER",owner),\
                 mock.patch.object(m,"UNIT",unit),\
                 mock.patch.object(m,"tailscale_status",return_value=sample),\
                 mock.patch.object(m,"_owned_cfon",return_value=True) as upstream_owner,\
                 mock.patch.object(m,"_socks_ready",return_value=None),\
                 mock.patch.object(m,"_port_open",return_value=False),\
                 mock.patch.object(m,"status",side_effect=mocked_status),\
                 mock.patch.object(m.subprocess,"run",side_effect=command):
                result=m.start("100.100.42.2","google.com\nbrave.com",1)
                self.assertTrue(result["ok"])
                self.assertEqual(result["peer"],"100.100.42.2")
                self.assertIn("Restart=no",unit.read_text())
                self.assertNotIn("WantedBy=",unit.read_text())
                self.assertEqual(owner.stat().st_mode & 0o777,0o600)
                self.assertTrue(json.loads(owner.read_text())["enabled"])
                self.assertTrue(upstream_owner.called)
                stopped=m.stop()
                self.assertTrue(stopped["ok"])
                self.assertTrue(stopped["upstreamPreserved"])
                self.assertFalse(json.loads(owner.read_text())["enabled"])
                self.assertTrue(any(cmd[-2:] == ("start",m.UNIT_NAME) for cmd in recorded))
                self.assertTrue(any(cmd[-2:] == ("stop",m.UNIT_NAME) for cmd in recorded))
                self.assertFalse(any("enable" in cmd for cmd in recorded))

    def test_explicit_service_identity_and_no_auto_enable(self):
        text=m._unit_text("100.100.42.1","100.100.42.2",30)
        self.assertIn("Restart=no",text)
        self.assertNotIn("WantedBy=",text)
        self.assertIn("NoNewPrivileges=yes",text)
        self.assertIn("RuntimeMaxSec=1800",text)
        self.assertIn("100.100.42.2",text)
        self.assertIn("100.100.42.1",text)
        with mock.patch.object(m,"tailscale_status",return_value={}):
            with self.assertRaises(m.TailnetError):
                m.start("100.100.42.2")
        # No call to systemctl was made by module import or the failed preflight.


if __name__=="__main__":
    unittest.main(verbosity=2)
