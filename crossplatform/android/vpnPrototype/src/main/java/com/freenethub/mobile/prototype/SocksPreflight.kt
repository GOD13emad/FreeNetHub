package com.freenethub.mobile.prototype

import java.io.BufferedInputStream
import java.io.IOException
import java.io.InputStream
import java.net.InetSocketAddress
import java.net.Socket
import java.nio.charset.StandardCharsets
import javax.net.ssl.SSLSocket
import javax.net.ssl.SSLSocketFactory

/**
 * No HTTP system proxy, no ambient Java ProxySelector, no HTTP redirects,
 * no cookies and no direct fallback. SOCKS resolves the remote DNS hostname.
 * This is a *prerequisite* for enabling the private VPN, not an IPv6/UDP test.
 */
internal object SocksPreflight {
    data class Result(val ok: Boolean, val detail: String)

    private fun exact(input: InputStream, length: Int): ByteArray {
        if (length !in 1..256) throw IOException("SOCKS_REPLY_LENGTH_INVALID")
        val dst = ByteArray(length)
        var offset = 0
        while (offset < length) {
            val n = input.read(dst, offset, length - offset)
            if (n < 0) throw IOException("SOCKS_REPLY_TRUNCATED")
            offset += n
        }
        return dst
    }

    private fun safeStatusLine(input: InputStream): String {
        val out = StringBuilder()
        for (i in 0 until 256) {
            val c = input.read()
            if (c < 0) throw IOException("TLS_HTTP_EMPTY_RESPONSE")
            if (c == 10) return out.toString().trimEnd('\r')
            if (c !in 32..126 && c != 13) throw IOException("TLS_HTTP_INVALID_RESPONSE")
            out.append(c.toChar())
        }
        throw IOException("TLS_HTTP_STATUS_TOO_LONG")
    }

    private fun probeOne(host: String) {
        val hostBytes = host.toByteArray(StandardCharsets.US_ASCII)
        if (hostBytes.size !in 3..253) throw IOException("INVALID_PROBE_HOST")
        Socket().use { socket ->
            socket.soTimeout = 7000
            socket.connect(InetSocketAddress(TunnelConfig.SOCKS_HOST, TunnelConfig.SOCKS_PORT), 3500)
            socket.getOutputStream().write(byteArrayOf(5, 1, 0))
            if (!exact(socket.getInputStream(), 2).contentEquals(byteArrayOf(5, 0))) {
                throw IOException("SOCKS5_NOAUTH_REFUSED")
            }
            socket.getOutputStream().write(
                byteArrayOf(5, 1, 0, 3, hostBytes.size.toByte()) + hostBytes +
                    byteArrayOf(1, 0xbb.toByte())
            )
            val reply = exact(socket.getInputStream(), 4)
            if (reply[0] != 5.toByte() || reply[1] != 0.toByte() ||
                reply[2] != 0.toByte()
            ) throw IOException("SOCKS5_REMOTE_CONNECT_REFUSED")
            val addrLen = when (reply[3].toInt() and 0xff) {
                1 -> 4
                4 -> 16
                3 -> exact(socket.getInputStream(), 1)[0].toInt() and 0xff
                else -> throw IOException("SOCKS5_ATYP_INVALID")
            }
            if (addrLen !in 1..253) throw IOException("SOCKS5_BIND_LENGTH")
            exact(socket.getInputStream(), addrLen + 2)

            val factory = SSLSocketFactory.getDefault() as SSLSocketFactory
            (factory.createSocket(socket, host, 443, true) as SSLSocket).use { tls ->
                tls.soTimeout = 7500
                val p = tls.sslParameters
                p.endpointIdentificationAlgorithm = "HTTPS"
                tls.sslParameters = p
                tls.startHandshake() // Trust manager + hostname identity, no exceptions swallowed.
                val request = "GET /generate_204 HTTP/1.1\r\n" +
                    "Host: " + host + "\r\nUser-Agent: FreeNetHub-USB-Probe\r\n" +
                    "Accept: */*\r\nConnection: close\r\n\r\n"
                tls.outputStream.write(request.toByteArray(StandardCharsets.US_ASCII))
                tls.outputStream.flush()
                val status = safeStatusLine(BufferedInputStream(tls.inputStream))
                if (status != "HTTP/1.1 204 No Content" &&
                    status != "HTTP/1.1 204" &&
                    !status.startsWith("HTTP/1.1 204 ")
                ) throw IOException("TLS_HTTPS_204_NOT_VERIFIED")
            }
        }
    }

    fun check(): Result {
        return try {
            // Independent target, not just a local SOCKS listener handshake.
            probeOne("www.google.com")
            probeOne("www.youtube.com")
            Result(true, "GOOGLE_YOUTUBE_SOCKS5_TLS_204_OK")
        } catch (e: Exception) {
            // Stable, non-sensitive category rather than spilling exception details.
            Result(false, when (e) {
                is java.net.SocketTimeoutException -> "UPSTREAM_TIMEOUT"
                is javax.net.ssl.SSLException -> "UPSTREAM_TLS_REJECTED"
                else -> (e.message ?: "UPSTREAM_UNAVAILABLE").take(96)
            })
        }
    }
}
