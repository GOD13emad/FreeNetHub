package com.freenethub.mobile
import android.app.Activity
import android.os.Bundle
import android.graphics.Color
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
class MainActivity: Activity() {
 override fun onCreate(savedInstanceState: Bundle?) {
  super.onCreate(savedInstanceState)
  val root=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(48,48,48,48); setBackgroundColor(Color.rgb(11,20,35)) }
  fun text(s:String,size:Float)=TextView(this).apply { text=s; textSize=size; setTextColor(Color.WHITE) }
  val status=text("Provider core: NOT LINKED. No TUN will be established.",16f)
  root.addView(text("FreeNet Hub 4.2.0",28f));root.addView(status)
  // Do not request VPN ownership while no forwarding core exists:
  // granting this permission may revoke another active VPN app.
  root.addView(Button(this).apply {
    text="VPN unavailable until forwarding core is linked"
    isEnabled=false
  })
  setContentView(root)
 }
}
