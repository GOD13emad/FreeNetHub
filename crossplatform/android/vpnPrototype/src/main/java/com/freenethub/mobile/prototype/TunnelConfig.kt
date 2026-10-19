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
    const val DNS_V4 = "1.1.1.1"
    const val DNS_V6 = "2606:4700:4700::1111"

    // Upstream UDP ASSOCIATE transport is not guaranteed through adb reverse.
    // Unsupported DNS/UDP packets must fail CLOSED rather than route DIRECT.
    fun nativeYaml(): String = """
        tunnel:
          mtu: 1500
          ipv4: 198.18.0.1
          ipv6: 'fd00:25::1'
          icmp: 'off'
        socks5:
          address: 127.0.0.1
          port: 19414
          udp: 'udp'
        misc:
          connect-timeout: 8000
          tcp-read-write-timeout: 60000
          udp-read-write-timeout: 12000
          max-session-count: 256
          log-file: null
          log-level: warn
    """.trimIndent() + "\n"
}
