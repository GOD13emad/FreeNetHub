package com.freenethub.mobile.prototype

import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.graphics.Color
import android.net.VpnService
import android.os.Bundle
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import hev.htproxy.TProxyService

/**
 * Separate, intentionally private opt-in executable.
 * No VpnService.prepare() until an explicit button tap, a fresh protected
 * SOCKS5+HTTPS preflight and a separate VPN-replacement warning confirmation.
 */
class MainActivity : Activity() {
    companion object { private const val PREPARE_VPN_REQUEST = 17423 }

    private lateinit var status: TextView
    private lateinit var connect: Button
    private lateinit var stop: Button
    private var checkedUpstream = false
    private var checking = false

    private fun nativeLoaded(): Boolean = try {
        TProxyService.TProxyIsRunning()
        true
    } catch (_: LinkageError) {
        false
    }

    private fun isRunning(): Boolean =
        try { TProxyService.TProxyIsRunning() } catch (_: LinkageError) { false }

    private fun refresh() {
        val active = isRunning()
        status.text = when {
            active -> "وضعیت: موتور Native در حال اجرا (DNS/UDP هنوز تأیید نشده)"
            checking -> "وضعیت: بررسی Google و YouTube از SOCKS محلی..."
            checkedUpstream -> "وضعیت: خروجی SOCKS+TLS تأیید شد؛ رضایت VPN هنوز لازم است"
            else -> "موتور Native خاموش است؛ برای رفع هر نشست مسدودشده، دکمه توقف را بزنید."
        }
        connect.isEnabled = checkedUpstream && !checking && !active
        stop.isEnabled = true // Always permit recovery if the native core stalled while TUN stayed open.
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val outer = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.rgb(10, 19, 34))
            setPadding(34, 40, 34, 30)
        }
        fun text(value: String, size: Float): TextView = TextView(this).apply {
            this.text = value
            textSize = size
            setTextColor(Color.WHITE)
            setPadding(0, 0, 0, 26)
        }
        outer.addView(text("FreeNet Hub — USB VPN Private Preview", 22f))
        outer.addView(text(
            "فقط آزمایش توسعه روی USB خودتان. برای کارکرد، Linux CFON باید روشن باشد " +
                "و ADB reverse tcp:19414 tcp:19414 به‌صورت مجاز برقرار شده باشد. " +
                "این نمونه جایگزین VPN فعلی می‌شود؛ Tailscale و VPN دیگر هم‌زمان کار نمی‌کنند. " +
                "UDP/DNS و پایداری هنوز تأیید نشده‌اند. نصب یا اتصال خودکار وجود ندارد.", 15f))
        status = text("", 16f)
        outer.addView(status)
        val check = Button(this).apply { text = "۱) بررسی مستقل SOCKS / Google / YouTube" }
        connect = Button(this).apply { text = "۲) درخواست رضایت بومی و اتصال VPN"; isEnabled = false }
        stop = Button(this).apply { text = "توقف فقط این نمونهٔ VPN"; isEnabled = false }
        outer.addView(check)
        outer.addView(connect)
        outer.addView(stop)
        outer.addView(text(
            "این نسخهٔ آزمایشی با شناسهٔ جدا نصب می‌شود و به FreeNet Hub عمومی " +
                "یا اطلاعات مرورگر شخصی دسترسی ندارد. خروج اینترنت در مسیر USB/CFON " +
                "اندازه‌گیری خواهد شد؛ هیچ تضمینی دربارهٔ UDP/IPv6 یا همهٔ برنامه‌ها داده نمی‌شود.", 13f))

        check.setOnClickListener {
            if (checking || !nativeLoaded()) {
                checkedUpstream = false
                status.text = "Native AAR موجود نیست یا بررسی قبلی هنوز اجرا می‌شود."
                refresh()
                return@setOnClickListener
            }
            checkedUpstream = false
            checking = true
            refresh()
            Thread({
                val result = SocksPreflight.check()
                runOnUiThread {
                    checking = false
                    checkedUpstream = result.ok
                    refresh()
                    if (!result.ok) status.text = "اتصال برقرار نشد: " + result.detail
                }
            }, "fnh-usb-socks-preflight").start()
        }
        connect.setOnClickListener {
            if (checking || !checkedUpstream || !nativeLoaded()) {
                checkedUpstream = false
                refresh()
                return@setOnClickListener
            }
            AlertDialog.Builder(this)
                .setTitle("تأیید آگاهانهٔ جایگزینی VPN")
                .setMessage(
                    "اتصال این برنامه می‌تواند VPN فعال دیگری را قطع کند. " +
                        "فقط اگر دستگاه و کابل USB متعلق به شماست و " +
                        "می‌خواهید آزمایش محدود را انجام دهید ادامه دهید. " +
                        "رضایت سیستم Android در مرحلهٔ بعد جداگانه درخواست می‌شود."
                )
                .setNegativeButton("انصراف", null)
                .setPositiveButton("درخواست مجوز رسمی Android") { _, _ ->
                    val intent = VpnService.prepare(this)
                    if (intent == null) {
                        startOwnedVpn()
                    } else {
                        startActivityForResult(intent, PREPARE_VPN_REQUEST)
                    }
                }.show()
        }
        stop.setOnClickListener {
            startService(Intent(this, PrivateVpnService::class.java).apply {
                action = PrivateVpnService.ACTION_STOP
            })
            checkedUpstream = false
            refresh()
        }
        setContentView(ScrollView(this).apply { addView(outer) })
        refresh()
    }

    private fun startOwnedVpn() {
        if (!checkedUpstream || !nativeLoaded()) {
            checkedUpstream = false
            refresh()
            return
        }
        startForegroundService(Intent(this, PrivateVpnService::class.java).apply {
            action = PrivateVpnService.ACTION_START
        })
        checkedUpstream = false
        status.text = "درخواست شروع ارسال شد؛ فقط پس از موفقیت Native، VPN برقرار است."
        refresh()
    }

    @Deprecated("Only used for the platform VPN consent Activity result.")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != PREPARE_VPN_REQUEST) return
        if (resultCode == RESULT_OK) startOwnedVpn()
        else {
            checkedUpstream = false
            refresh()
        }
    }

    override fun onResume() {
        super.onResume()
        if (::status.isInitialized) refresh()
    }
}
