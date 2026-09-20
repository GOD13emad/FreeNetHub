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
  root.addView(text("FreeNet Hub 4.1.1",28f));root.addView(status)
  root.addView(Button(this).apply { text="Request VPN permission"; setOnClickListener {
    val i=android.net.VpnService.prepare(this@MainActivity)
    if(i!=null) startActivityForResult(i,1001) else status.text="Permission ready; provider core still NOT LINKED."
  }})
  setContentView(root)
 }
}
