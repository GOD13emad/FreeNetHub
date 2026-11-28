using System;
using System.IO;
using System.Reflection;
public class ShellLaunchContractTest {
    static int passed=0;
    static void Yes(bool condition,string message) {
        if(!condition) throw new Exception("TEST_FAIL "+message);
        ++passed;
    }
    static void No(string[] args,string message) {
        bool rejected=false;
        try { Program.ResolveTrustedEntry(args); }
        catch(ArgumentException) { rejected=true; }
        catch(UnauthorizedAccessException) { rejected=true; }
        catch(IOException) { rejected=true; }
        Yes(rejected,message);
    }
    public static int Main() {
        string root=AppDomain.CurrentDomain.BaseDirectory;
        string folder=Path.Combine(root,"app");
        Directory.CreateDirectory(folder);
        string path=Path.Combine(folder,"FreeNetHub.ps1");
        File.WriteAllText(path,"# test fixture only");
        string external=Path.Combine(root,"other.ps1");
        File.WriteAllText(external,"# not an authorized entry");
        Yes(Program.ResolveTrustedEntry(new string[0])==Path.GetFullPath(path),"implicit accepted");
        Yes(Program.ResolveTrustedEntry(new string[]{path})==Path.GetFullPath(path),"explicit accepted");
        Yes(Program.ResolveTrustedEntry(new string[]{Path.Combine(folder,".","FreeNetHub.ps1")})==Path.GetFullPath(path),"normalized accepted");
        Yes(Program.ResolveTrustedEntry(new string[]{path.ToUpperInvariant()})==Path.GetFullPath(path),"case-insensitive accepted");
        No(new string[]{external},"alternate file rejected");
        No(new string[]{Path.Combine(root,"app","..","other.ps1")},"traversal rejected");
        No(new string[]{path,"extra"},"extra arguments rejected");
        No(new string[]{""},"empty argument rejected");
        No(new string[]{path+"\" -Command Write-Output exploit"},"quote-bearing command rejected");
        No(new string[]{"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\profile.ps1"},"external script rejected");
        var mi=typeof(Program).GetMethod("DiscoverPowerShell",BindingFlags.NonPublic|BindingFlags.Static);
        Yes(mi!=null,"PowerShell resolver present");
        string resolved=(string)mi.Invoke(null,null);
        string pf=Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
        Yes(Path.GetFullPath(resolved).StartsWith(Path.GetFullPath(Path.Combine(pf,"PowerShell"))+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase),"PowerShell limited to Program Files");
        Console.WriteLine("SHELL_CONTRACT_TEST_PASS "+passed+"/12 - policy only; no launched PowerShell or UI");
        return 0;
    }
}
