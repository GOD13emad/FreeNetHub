package com.freenethub.mobile.prototype

/**
 * Deliberately limited to localhost so an unauthenticated public SOCKS proxy
 * cannot be mistaken for a secure VPN server. adb reverse forwards this
 * TCP-only endpoint over the owner's authorized USB cable to Linux CFON.
 */
internal object TunnelConfig {
    const val SOCKS_HOST = "127.0.0.1"
    const val SOCKS_PORT = 19414
    const val MTU = 1500
    const val VPN_V4 = "198.18.0.1"
    const val VPN_V6 = "fd00:25::1"
    // HEV Mapped DNS answers IPv4 A locally and restores hostnames on SOCKS
    // CONNECT. No public UDP DNS resolver is advertised via Android Builder.
    const val MAPPED_DNS_V4 = "198.18.0.2"
    const val MAPPED_FAKE_V4_NETWORK = "198.19.0.0"
    const val MAPPED_FAKE_V4_MASK = "255.255.0.0"
    const val MAPPED_FAKE_V4_CACHE = 8192

    // CRITICAL: UDP_IN_UDP creates a direct OS SOCK_DGRAM relay socket.
    // Our UID is excluded from VPN routing, so that socket could leave over
    // the phone's own network. Force HEV UDP_IN_TCP instead: extension may
    // be unsupported by CFON, then UDP fails closed inside the SOCKS stream.
    fun nativeYaml(): String = """
        tunnel:
          mtu: 1500
          ipv4: 198.18.0.1
          ipv6: 'fd00:25::1'
          icmp: 'off'
        socks5:
          address: 127.0.0.1
          port: 19414
          udp: 'tcp'
        # Only IPv4 A DNS is synthesized. Native maps the synthetic address
        # back to the original name before SOCKS CONNECT. UDP/AAAA unverified.
        mapdns:
          address: 198.18.0.2
          port: 53
          network: 198.19.0.0
          netmask: 255.255.0.0
          cache-size: 8192
        misc:
          connect-timeout: 8000
          tcp-read-write-timeout: 60000
          udp-read-write-timeout: 12000
          max-session-count: 256
          log-file: null
          log-level: warn
    """.trimIndent() + "\n"
}
