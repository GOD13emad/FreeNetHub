package com.freenethub.mobile
import android.net.VpnService
class FreeNetVpnService: VpnService() {
 fun providerCoreReady(): Boolean = false
 // Builder.establish() is intentionally absent until a real forwarding core is integrated and tested.
}
