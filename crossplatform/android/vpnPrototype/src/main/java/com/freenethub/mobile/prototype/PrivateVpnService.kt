package com.freenethub.mobile.prototype

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.net.VpnService
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.ParcelFileDescriptor
import android.util.Log
import hev.htproxy.TProxyService
import java.io.File
import java.util.concurrent.Executors

/**
 * PRIVATE USB-only, opt-in TUN -> native tun2socks.
 *
 * No boot receiver, automatic reconnect, or permission bypass. Preflight
 * happens BEFORE Builder.establish. The upstream is localhost-only and the
 * app's own UID is excluded to prevent the native SOCKS connection recursing.
 *
 * Native hev 2.18.0 leaves EXTERN_TUN_FD ownership to its Android caller
 * (tunnel_fini skips close when tun_fd_local is false), so ParcelFileDescriptor
 * stays owned here and is closed AFTER TProxyStopService.
 */
class PrivateVpnService : VpnService() {
    companion object {
        const val ACTION_START = "com.freenethub.mobile.prototype.START"
        const val ACTION_STOP = "com.freenethub.mobile.prototype.STOP"
        private const val CHANNEL_ID = "fnh_private_usb_vpn"
        private const val NOTIFICATION_ID = 17423
        private const val TAG = "FNH-PrivateVpn"
    }

    // Private QA breadcrumbs only: no credentials, domains, packet contents or user data.
    // The file survives a scoped app force-stop and can be read with run-as in
    // this debug-only prototype, so native startup failures are reproducible.
    private fun qaStage(stage: String, failure: Boolean = false) {
        try {
            val prefs = getSharedPreferences("fnh_private_native_qa", MODE_PRIVATE)
            val edit = prefs.edit()
                .putString("last_phase", stage)
                .putLong("last_phase_epoch_ms", System.currentTimeMillis())
            if (stage == "START_REQUESTED") {
                edit.remove("last_failure")
                    .putBoolean("tun_reached", false)
                    .putBoolean("native_reached", false)
            }
            if (stage == "TUN_ESTABLISHED") edit.putBoolean("tun_reached", true)
            if (stage == "NATIVE_ENGINE_RUNNING") edit.putBoolean("native_reached", true)
            if (failure) edit.putString("last_failure", stage)
            edit.commit()
        } catch (_: RuntimeException) {
            // Debug-only telemetry may never affect tunnel or cleanup paths.
        }
        Log.i(TAG, "QA_STAGE_" + stage)
    }

    private val lifecycle = Any()
    private val worker = Executors.newSingleThreadExecutor()
    private val handler = Handler(Looper.getMainLooper())
    @Volatile private var cancellation = false
    private var connecting = false
    private var nativeRunning = false
    private var tun: ParcelFileDescriptor? = null
    private var config: File? = null
    private var foregroundActive = false

    private val watchdog = object : Runnable {
        override fun run() {
            if (cancellation) return
            val healthy = try {
                TProxyService.TProxyIsRunning()
            } catch (_: LinkageError) { false }
            if (!healthy) {
                // Keep the TUN open and black-hole the affected traffic rather
                // than silently restoring DIRECT if the native core crashed.
                // The notification's STOP action is always available.
                Log.e(TAG, "NATIVE_EXIT_TUN_STILL_BLOCKING_USER_MUST_STOP")
                return
            }
            handler.postDelayed(this, 5_000)
        }
    }

    private fun notification(): Notification {
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_ID,
                "FreeNet Hub private USB VPN",
                NotificationManager.IMPORTANCE_LOW
            )
        )
        val stopAction = Intent(this, PrivateVpnService::class.java).apply { action = ACTION_STOP }
        val stopPending = PendingIntent.getService(
            this, 2, stopAction, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val showPending = PendingIntent.getActivity(
            this, 1, Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        return Notification.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_sys_upload)
            .setContentTitle("FreeNet Hub — PRIVATE USB VPN")
            .setContentText("آزمایش محدود TUN/SOCKS؛ توقف در هر لحظه")
            .setContentIntent(showPending)
            .setOngoing(true)
            .addAction(android.R.drawable.ic_menu_close_clear_cancel, "توقف این VPN", stopPending)
            .build()
    }

    private fun startForegroundSafely(): Boolean {
        return try {
            val notice = notification()
            if (Build.VERSION.SDK_INT >= 34) {
                startForeground(
                    NOTIFICATION_ID, notice, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE
                )
            } else {
                startForeground(NOTIFICATION_ID, notice)
            }
            foregroundActive = true
            true
        } catch (e: RuntimeException) {
            Log.w(TAG, "FOREGROUND_PERMISSION_OR_POLICY_REJECTED", e)
            false
        }
    }

    private fun buildPrivateTun(): ParcelFileDescriptor {
        val builder = Builder()
            .setSession("FreeNet Hub - PRIVATE USB SOCKS")
            .setMtu(TunnelConfig.MTU)
            .addAddress(TunnelConfig.VPN_V4, 15)
            .addAddress(TunnelConfig.VPN_V6, 64)
            .addRoute("0.0.0.0", 0)
            .addRoute("::", 0)
            // The HEV mapdns destination is intercepted inside the TUN.
            // Remote SOCKS resolves the original domain for IPv4 A queries.
            // Avoid publishing public IPv4/IPv6 DNS upstream addresses here.
            .addDnsServer(TunnelConfig.MAPPED_DNS_V4)
            .setBlocking(false)
        // Native SOCKS sockets are created by this app's UID. Exclude ONLY this
        // UID from the TUN; otherwise the upstream can loop back into the VPN.
        builder.addDisallowedApplication(packageName)
        return builder.establish() ?: throw IllegalStateException("VPN_ESTABLISH_REFUSED")
    }

    private fun startOwned() {
        synchronized(lifecycle) {
            if (connecting || nativeRunning) return
            if (VpnService.prepare(this) != null) {
                qaStage("ABORT_VPN_CONSENT_NOT_GRANTED", true)
                Log.w(TAG, "VPN_SYSTEM_CONSENT_NOT_GRANTED")
                stopSelf()
                return
            }
            if (Build.VERSION.SDK_INT >= 29 && isLockdownEnabled) {
                // Never override user/device policy or silently bypass lockdown.
                qaStage("ABORT_LOCKDOWN_POLICY", true)
                Log.w(TAG, "LOCKDOWN_VPN_POLICY_UNSUPPORTED_IN_PRIVATE_PROTOTYPE")
                stopSelf()
                return
            }
            cancellation = false
            connecting = true
        }
        if (!startForegroundSafely()) {
            qaStage("ABORT_FOREGROUND_START", true)
            stopOwned()
            return
        }
        worker.execute {
            try {
                qaStage("SOCKS_PREFLIGHT_STARTED")
                val upstream = SocksPreflight.check()
                if (!upstream.ok) {
                    qaStage("ABORT_SOCKS_PREFLIGHT", true)
                    throw IllegalStateException("SOCKS_TLS_PREFLIGHT_" + upstream.detail)
                }
                qaStage("SOCKS_PREFLIGHT_PASSED")
                synchronized(lifecycle) {
                    if (cancellation) return@execute
                    val descriptor = buildPrivateTun()
                    tun = descriptor
                    qaStage("TUN_ESTABLISHED")
                    val file = File(cacheDir, "fnh-private-hev.yaml")
                    file.writeText(TunnelConfig.nativeYaml(), Charsets.UTF_8)
                    file.setReadable(false, false)
                    file.setReadable(true, true)
                    config = file
                    if (!TProxyService.TProxyStartService(file.absolutePath, descriptor.fd)) {
                        throw IllegalStateException("NATIVE_START_REFUSED")
                    }
                    nativeRunning = true
                    qaStage("NATIVE_ENGINE_STARTED")
                }
                Thread.sleep(400)
                if (cancellation || !TProxyService.TProxyIsRunning()) {
                    throw IllegalStateException("NATIVE_START_NOT_STABLE")
                }
                qaStage("NATIVE_ENGINE_RUNNING")
                synchronized(lifecycle) { connecting = false }
                handler.post { if (!cancellation) handler.postDelayed(watchdog, 5_000) }
            } catch (e: InterruptedException) {
                qaStage("ABORT_WORKER_INTERRUPTED", true)
                handler.post { stopOwned() }
                Thread.currentThread().interrupt()
            } catch (e: Exception) {
                qaStage("ABORT_" + e.javaClass.simpleName, true)
                Log.w(TAG, "PRIVATE_FORWARDER_START_ABORT", e)
                handler.post { stopOwned() }
            } catch (e: LinkageError) {
                qaStage("ABORT_NATIVE_LINKAGE", true)
                Log.w(TAG, "PINNED_NATIVE_LIBRARY_NOT_AVAILABLE", e)
                handler.post { stopOwned() }
            }
        }
    }

    /**
     * Stops ONLY our process-owned native library, then closes our TUN FD.
     * Does not modify system routes, other VPN apps or user's proxy settings.
     */
    private fun stopOwned() {
        qaStage("STOP_REQUESTED")
        synchronized(lifecycle) {
            cancellation = true
            connecting = false
            handler.removeCallbacks(watchdog)
            if (nativeRunning) {
                try {
                    if (!TProxyService.TProxyStopService())
                        Log.w(TAG, "NATIVE_STOP_WAS_NOT_CONFIRMED")
                } catch (e: LinkageError) {
                    Log.w(TAG, "NATIVE_STOP_LINKAGE_ERROR", e)
                }
                nativeRunning = false
            }
            try { tun?.close() } catch (e: Exception) {
                Log.w(TAG, "OWNED_TUN_FD_CLOSE_FAILED", e)
            }
            tun = null
            config?.delete()
            config = null
        }
        if (foregroundActive) {
            stopForeground(Service.STOP_FOREGROUND_REMOVE)
            foregroundActive = false
        }
        qaStage("STOP_CLEANUP_DONE")
        stopSelf()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                qaStage("START_REQUESTED")
                startOwned()
            }
            ACTION_STOP -> stopOwned()
            else -> { Log.w(TAG, "NO_IMPLICIT_VPN_START"); stopSelf() }
        }
        return START_NOT_STICKY
    }

    override fun onRevoke() {
        stopOwned()
        super.onRevoke()
    }

    override fun onDestroy() {
        stopOwned()
        worker.shutdownNow()
        super.onDestroy()
    }
}
