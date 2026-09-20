using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;
using System.Reflection;

[assembly: AssemblyTitle("FreeNet Hub")]
[assembly: AssemblyProduct("FreeNet Hub")]
[assembly: AssemblyDescription("Standalone desktop shell for FreeNet Hub")]
[assembly: AssemblyCompany("FreeNet Hub")]
[assembly: AssemblyVersion("4.1.1.0")]
[assembly: AssemblyFileVersion("4.1.1.0")]

internal static class Native
{
    public const int SW_HIDE=0, SW_SHOWNORMAL=1, SW_SHOW=5, SW_RESTORE=9;
    public const int WM_SETICON=0x0080, ICON_SMALL=0, ICON_BIG=1;
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowTextLength(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern IntPtr SendMessage(IntPtr hWnd,int msg,IntPtr wParam,IntPtr lParam);
    [DllImport("shell32.dll", SetLastError=true)] public static extern int SetCurrentProcessExplicitAppUserModelID([MarshalAs(UnmanagedType.LPWStr)] string AppID);

    [StructLayout(LayoutKind.Sequential, Pack=4)] public struct PROPERTYKEY { public Guid fmtid; public uint pid; public PROPERTYKEY(Guid f,uint p){fmtid=f;pid=p;} }
    [StructLayout(LayoutKind.Explicit)] public struct PROPVARIANT { [FieldOffset(0)] public ushort vt; [FieldOffset(8)] public IntPtr pointerValue; }
    [ComImport, Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    public interface IPropertyStore { uint GetCount(); PROPERTYKEY GetAt(uint i); void GetValue(ref PROPERTYKEY key, out PROPVARIANT pv); void SetValue(ref PROPERTYKEY key, ref PROPVARIANT pv); void Commit(); }
    [DllImport("shell32.dll")] public static extern int SHGetPropertyStoreForWindow(IntPtr hwnd, ref Guid iid, [Out, MarshalAs(UnmanagedType.Interface)] out IPropertyStore propertyStore);

    public static void SetWindowAppId(IntPtr hwnd, string appId)
    {
        try {
            Guid iid = new Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99");
            IPropertyStore store;
            if (SHGetPropertyStoreForWindow(hwnd, ref iid, out store) != 0 || store == null) return;
            var key = new PROPERTYKEY(new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"), 5);
            var pv = new PROPVARIANT { vt = 31, pointerValue = Marshal.StringToCoTaskMemUni(appId) };
            try { store.SetValue(ref key, ref pv); store.Commit(); }
            finally { Marshal.FreeCoTaskMem(pv.pointerValue); }
        } catch { }
    }

    public static IntPtr FindTopLevelWindowForProcess(int pid)
    {
        IntPtr found=IntPtr.Zero;
        EnumWindows(delegate(IntPtr h, IntPtr l) {
            uint p; GetWindowThreadProcessId(h,out p);
            if(p==(uint)pid && IsWindow(h) && IsWindowVisible(h) && GetWindowTextLength(h)>0) { found=h; return false; }
            return true;
        }, IntPtr.Zero);
        return found;
    }
}

internal sealed class ShellContext : ApplicationContext
{
    const string AppId="FreeNetHub.Desktop";
    readonly NotifyIcon tray;
    readonly System.Windows.Forms.Timer timer;
    readonly EventWaitHandle activationEvent;
    readonly string script;
    readonly string powershell;
    readonly Icon icon;
    Process child;
    IntPtr hwnd=IntPtr.Zero;
    bool balloonShown=false;
    int exitCode=0;

    public ShellContext(string scriptPath, string powershellPath, EventWaitHandle activation)
    {
        script=scriptPath; powershell=powershellPath; activationEvent=activation;
        icon=LoadAppIcon();
        tray=new NotifyIcon();
        tray.Visible=true; tray.Icon=icon; tray.Text="FreeNet Hub";
        var menu=new ContextMenuStrip();
        menu.RightToLeft=RightToLeft.Yes;
        menu.Items.Add("باز کردن FreeNet Hub",null,delegate{Restore();});
        menu.Items.Add("راه‌اندازی مجدد رابط",null,delegate{Restart();});
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add("خروج کامل",null,delegate{ExitAll(0);});
        tray.ContextMenuStrip=menu;
        tray.DoubleClick+=delegate{Restore();};
        timer=new System.Windows.Forms.Timer(); timer.Interval=250; timer.Tick+=delegate{Tick();};
        StartChild(); timer.Start();
    }

    static Icon LoadAppIcon()
    {
        try {
            var p=Application.ExecutablePath;
            var i=Icon.ExtractAssociatedIcon(p);
            if(i!=null) return (Icon)i.Clone();
        } catch { }
        return SystemIcons.Application;
    }

    void StartChild()
    {
        if(!File.Exists(script)) { MessageBox.Show("فایل رابط FreeNet Hub پیدا نشد:\n"+script,"FreeNet Hub",MessageBoxButtons.OK,MessageBoxIcon.Error); ExitAll(2); return; }
        if(!File.Exists(powershell)) { MessageBox.Show("PowerShell 7 پیدا نشد:\n"+powershell,"FreeNet Hub",MessageBoxButtons.OK,MessageBoxIcon.Error); ExitAll(3); return; }
        var psi=new ProcessStartInfo();
        psi.FileName=powershell;
        psi.UseShellExecute=false;
        psi.CreateNoWindow=true;
        psi.WindowStyle=ProcessWindowStyle.Hidden;
        psi.Arguments="-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -STA -File \""+script.Replace("\"","\\\"")+"\"";
        psi.WorkingDirectory=Path.GetDirectoryName(script);
        psi.EnvironmentVariables["FREENETHUB_SHELL_HOST"]="1";
        child=Process.Start(psi);
        hwnd=IntPtr.Zero; balloonShown=false;
    }

    IntPtr ResolveWindow()
    {
        if(child==null || child.HasExited) return IntPtr.Zero;
        try { child.Refresh(); if(child.MainWindowHandle!=IntPtr.Zero) return child.MainWindowHandle; } catch { }
        return Native.FindTopLevelWindowForProcess(child.Id);
    }

    void ApplyWindowIdentity(IntPtr h)
    {
        if(h==IntPtr.Zero) return;
        Native.SetWindowAppId(h,AppId);
        Native.SendMessage(h,Native.WM_SETICON,(IntPtr)Native.ICON_BIG,icon.Handle);
        Native.SendMessage(h,Native.WM_SETICON,(IntPtr)Native.ICON_SMALL,icon.Handle);
    }

    void Tick()
    {
        // Second Start-menu launch signals this event and restores the existing instance.
        try { if(activationEvent.WaitOne(0)) Restore(); } catch { }
        if(child==null) return;
        if(child.HasExited) {
            int code=0; try{code=child.ExitCode;}catch{}
            if(code==0) { ExitAll(0); return; }
            timer.Stop();
            tray.Text="FreeNet Hub — رابط متوقف شده";
            tray.ShowBalloonTip(2500,"FreeNet Hub","رابط به‌طور غیرمنتظره بسته شد. از منوی Tray می‌توانید آن را دوباره اجرا کنید.",ToolTipIcon.Warning);
            return;
        }
        var resolved=ResolveWindow();
        if(resolved!=IntPtr.Zero && resolved!=hwnd) {
            hwnd=resolved;
            ApplyWindowIdentity(hwnd);
        } else if(hwnd==IntPtr.Zero || !Native.IsWindow(hwnd)) {
            hwnd=resolved;
            if(hwnd!=IntPtr.Zero) ApplyWindowIdentity(hwnd);
        }
        if(hwnd!=IntPtr.Zero && Native.IsIconic(hwnd)) HideToTray();
    }

    void HideToTray()
    {
        if(hwnd==IntPtr.Zero) return;
        Native.ShowWindow(hwnd,Native.SW_HIDE);
        if(!balloonShown) {
            balloonShown=true;
            tray.ShowBalloonTip(1300,"FreeNet Hub","برنامه در System Tray فعال است. برای بازگشت روی آیکون دوبار کلیک کنید.",ToolTipIcon.Info);
        }
    }

    void Restore()
    {
        if(child==null || child.HasExited) { StartChild(); timer.Start(); return; }
        if(hwnd==IntPtr.Zero || !Native.IsWindow(hwnd)) hwnd=ResolveWindow();
        if(hwnd==IntPtr.Zero) return;
        ApplyWindowIdentity(hwnd);
        Native.ShowWindow(hwnd,Native.SW_RESTORE);
        Native.ShowWindow(hwnd,Native.SW_SHOW);
        Native.BringWindowToTop(hwnd);
        Native.SetForegroundWindow(hwnd);
    }

    void Restart()
    {
        try { if(child!=null && !child.HasExited) child.Kill(); } catch { }
        Thread.Sleep(250);
        StartChild(); timer.Start();
    }

    void ExitAll(int code)
    {
        exitCode=code;
        timer.Stop();
        try { if(child!=null && !child.HasExited) child.Kill(); } catch { }
        tray.Visible=false;
        ExitThread();
    }

    protected override void ExitThreadCore()
    {
        tray.Visible=false;
        base.ExitThreadCore();
        Environment.ExitCode=exitCode;
    }

    protected override void Dispose(bool disposing)
    {
        if(disposing) { try{timer.Dispose();}catch{} try{tray.Dispose();}catch{} try{icon.Dispose();}catch{} }
        base.Dispose(disposing);
    }
}

internal static class Program
{
    const string MutexName="Local\\FreeNetHub.Desktop.SingleInstance.v41";
    const string EventName="Local\\FreeNetHub.Desktop.Activate.v41";
    [STAThread]
    static void Main(string[] args)
    {
        bool first;
        using(var mutex=new Mutex(true,MutexName,out first)) {
            if(!first) {
                try { using(var e=EventWaitHandle.OpenExisting(EventName)) e.Set(); } catch { }
                return;
            }
            bool created;
            using(var activation=new EventWaitHandle(false,EventResetMode.AutoReset,EventName,out created)) {
                try { Native.SetCurrentProcessExplicitAppUserModelID("FreeNetHub.Desktop"); } catch { }
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                string script=args.Length>0 ? args[0] : DiscoverScript();
                string ps=DiscoverPowerShell();
                Application.Run(new ShellContext(script,ps,activation));
            }
        }
    }

    static string DiscoverPowerShell()
    {
        string[] candidates=new string[] {
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),"PowerShell","7","pwsh.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),"PowerShell","7-preview","pwsh.exe")
        };
        foreach(var p in candidates) if(File.Exists(p)) return p;
        string path=Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach(var dir in path.Split(';')) { try { var p=Path.Combine(dir.Trim(),"pwsh.exe"); if(File.Exists(p)) return p; } catch{} }
        return candidates[0];
    }

    static string DiscoverScript()
    {
        string root=AppDomain.CurrentDomain.BaseDirectory;
        string[] candidates=new string[] {Path.Combine("app","FreeNetHub.ps1"),"FreeNetHub.ps1","App.ps1","app.ps1",Path.Combine("App","App.ps1"),Path.Combine("src","App.ps1")};
        foreach(var c in candidates) { var p=Path.Combine(root,c); if(File.Exists(p)) return p; }
        return Path.Combine(root,"App.ps1");
    }
}
