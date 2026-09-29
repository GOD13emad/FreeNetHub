[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$Interface='Ethernet 3'
$Primary='76.76.10.11'
$Previous=@((Get-DnsClientServerAddress -InterfaceAlias $Interface -AddressFamily IPv4).ServerAddresses)
try{
  Set-DnsClientServerAddress -InterfaceAlias $Interface -ServerAddresses @($Primary)
  Clear-DnsClientCache
  Start-Sleep -Seconds 2
  $rows=@()
  foreach($name in @('www.youtube.com','github.com','api.openai.com','www.youtube.com','github.com','api.openai.com')){
    $sw=[Diagnostics.Stopwatch]::StartNew()
    try{
      $a=@([System.Net.Dns]::GetHostAddresses($name)|Where-Object AddressFamily -eq InterNetwork|ForEach-Object IPAddressToString|Select-Object -Unique)
      $ok=$a.Count -gt 0
      $err=''
    }catch{$a=@();$ok=$false;$err=$_.Exception.Message}
    $sw.Stop()
    $rows+=[pscustomobject]@{name=$name;ok=$ok;ms=$sw.ElapsedMilliseconds;answers=$a;error=$err}
    Clear-DnsClientCache
    Start-Sleep -Milliseconds 250
  }
  $urls=@('https://www.youtube.com/generate_204','https://api.openai.com/v1/models','https://github.com/')
  $http=@()
  foreach($u in $urls){
    $m=& curl.exe -4 --noproxy '*' -sS -o NUL -w '%{http_code}|%{remote_ip}|%{time_total}' --max-time 5 $u 2>&1
    $http+=[pscustomobject]@{url=$u;exit=$LASTEXITCODE;meta=($m -join ' ')}
  }
  [pscustomobject]@{previous=$Previous;current=@((Get-DnsClientServerAddress -InterfaceAlias $Interface -AddressFamily IPv4).ServerAddresses);dns=$rows;http=$http}|ConvertTo-Json -Depth 8
}catch{
  Set-DnsClientServerAddress -InterfaceAlias $Interface -ServerAddresses $Previous -ErrorAction SilentlyContinue
  Clear-DnsClientCache -ErrorAction SilentlyContinue
  throw
}