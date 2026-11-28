"""Offline verified TLS diagnostic contract; no real socket is opened."""
import importlib.util
from pathlib import Path
import socket
import ssl
import unittest
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location('r34_probe', Path(__file__).with_name('r34_sni_probe.py'))
probe = importlib.util.module_from_spec(spec)
with patch('socket.getaddrinfo', side_effect=AssertionError('network')), patch('socket.socket', side_effect=AssertionError('network')):
    spec.loader.exec_module(probe)


class VerifiedProbeTests(unittest.TestCase):
    def setUp(self):
        dns = patch.object(probe.socket, 'getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 0, '', ('192.0.2.1', 443))])
        self.dns = dns.start()
        self.addCleanup(dns.stop)
        sock = patch.object(probe.socket, 'socket')
        self.sock = sock.start()
        self.addCleanup(sock.stop)
        self.raw = self.sock.return_value.__enter__.return_value
        self.ctx = MagicMock(check_hostname=True, verify_mode=ssl.CERT_REQUIRED)
        context = patch.object(probe.ssl, 'create_default_context', return_value=self.ctx)
        context.start()
        self.addCleanup(context.stop)
        conn = self.ctx.wrap_socket.return_value.__enter__.return_value
        conn.version.return_value = 'TLSv1.3'
        conn.cipher.return_value = ('TEST',)

    def test_verified(self):
        self.assertTrue(probe.probe('example.invalid')['tls'])
        self.ctx.wrap_socket.assert_called_once_with(self.raw, server_hostname='example.invalid')
        self.assertEqual(self.ctx.minimum_version, ssl.TLSVersion.TLSv1_2)

    def test_real_context_policy_without_network(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with patch.object(probe.ssl, 'create_default_context', return_value=context), patch.object(context, 'wrap_socket', side_effect=ssl.SSLError('synthetic handshake stop')) as wrap:
            self.assertFalse(probe.probe('example.invalid')['tls'])
            self.assertTrue(context.check_hostname)
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertEqual(context.minimum_version, ssl.TLSVersion.TLSv1_2)
            wrap.assert_called_once()

    def test_cert_rejected(self):
        self.ctx.wrap_socket.side_effect = ssl.SSLCertVerificationError('synthetic certificate rejection')
        self.assertFalse(probe.probe('example.invalid')['tls'])
        self.sock.return_value.__exit__.assert_called_once()

    def test_bad_policy(self):
        self.ctx.check_hostname = False
        self.assertFalse(probe.probe('example.invalid')['tls'])
        self.ctx.wrap_socket.assert_not_called()

    def test_dns_failure(self):
        self.dns.side_effect = socket.gaierror('synthetic')
        self.assertIn('resolveError', probe.probe('example.invalid'))
        self.sock.assert_not_called()

    def test_connect_failure(self):
        self.raw.connect.side_effect = OSError('synthetic')
        self.assertFalse(probe.probe('example.invalid')['tls'])
        self.ctx.wrap_socket.assert_not_called()
        self.sock.return_value.__exit__.assert_called_once()


if __name__ == '__main__':
    unittest.main()
